import ast
import re

import numpy as np
from scipy.interpolate import interp1d

import devices as dev
import UserFunc as uf
import logging
import os
import Parser as prs
#import ThermoLog
#ThermoLog.setup_logger('solverLog', 'info.log',logging.DEBUG)

solverLog=logging.getLogger('solverLog')



DEBUG = False
SKIP_FUNCS = False


class Preloader():
    preInitialData = {} #кривой костыль для предварительного чтения данных из файла пользователя, нужно, чтобы предварительно считать пути, по ктоторым хранятся характеристики узлов, в потом их передать в getCompressorMap
    nodeTypes = {}
    currentSectionName = ""
    funcParams = {}
    funcs = {}

    def __init__(self, fileName, initialData): #сюда передается имя файла с моделью, не input_data!!!
        text = open(fileName, 'r').readlines()
        initialData['Rezults']={}
        for t in text:
            line = t.strip()

            if len(line) == 0:
                continue
            if line[0] == '#':
                continue
            if line[0] == '{':
                res = re.match(r"^.*{(.+)}.*$", line)
                self.currentSectionName = res.group(1)
                if DEBUG:
                    print(f"[section {self.currentSectionName}]")
                continue
            if line.find('=') != -1:
                a = line.split('=', 1)
                a[0] = a[0].strip()
                a[1] = a[1].strip()
                #if a[1].find(r"'") != -1 or a[1].find('"') != -1:
                 #   self.preInitialData[a[0]] = str(a[1].strip('"\''))
                #else:
                #    self.preInitialData[a[0]] = float(a[1])
                var_name = a[0].strip()
                if self.currentSectionName in ['Parameters', 'Composition_of_inlet_gas', 'Secondary air system', 'Maps']:
                    if (a[1].strip() in ['nan', 'np.nan', 'NaN']):
                        var_val = np.nan
                    else:
                        var_val = ast.literal_eval(a[1].strip())

                    self.preInitialData[var_name] = var_val

                # if self.currentSectionName == 'Calculated parameters':
                #     line = line.replace(' ', '')
                #     # res = re.match(r'(\S+)\ *=\ *(\S+)\ *\(\s*(.+)\s*\)', line)
                #     res = re.match(r'(\S+)\ *={1}(?:\ *(\S+)\ *\(\s*(.+)\s*\)|\ *(\d+\.*\d*)\ *)',line)
                #
                #     if res == None: # constant
                #         initialData[a[0]] = uf.UserFunction(a[0], "", "", a[1], 3)
                #     else:
                #         paramName = res.group(1)
                #         if res.group(2)==None:
                #             paramValue=res.group(4)
                #             initialData[paramName] = paramValue
                #         else:
                #             paramFunc = res.group(2)
                #             funcArg = res.group(3)
                #             if funcArg[0] == '[' and funcArg[-1] == ']':
                #                 self.funcs[paramFunc].params = list(funcArg[1:-1].split(','))
                #             else:
                #                 self.funcs[paramFunc].params = funcArg
                #             if paramFunc in self.funcs:
                #                 initialData[paramName] = self.funcs[paramFunc]
                #             else:
                #                 print("ERROR") # what i am doing here
                if self.currentSectionName == "Parameters":
                    initialData[var_name] = var_val
                if self.currentSectionName == "Composition_of_inlet_gas":
                    initialData[var_name] = np.array(var_val)
                if self.currentSectionName == "Secondary air system":
                    initialData[var_name] = var_val
                # if self.currentSectionName == "Auxiliary functions":
                #     res = re.match(r'(\(.*\)),(\(.*\))', a[1])
                #     funcDecl = res.group(1)[1:-1]
                #     funcParam = res.group(2)[1:-1]
                #     _uf = uf.UserFunction(a[0], a[0], funcDecl, funcParam, 1)
                #     initialData[var_name] = _uf
                #     continue
                if self.currentSectionName == "Functions":
                    _func_object=prs.Parser_formula()
                    _func_object.prepare_formula(line.split('#',1)[0].strip())
                    f_name = re.match(r'(\S+)\((\S+)\)', a[0])
                    funcName = f_name.group(1)
                    # funcDecl = a[1]
                    # _uf = uf.UserFunction(funcName, a[0], funcDecl, None, 2)
                    self.funcs[funcName] = _func_object
                    continue
                if a[0] in self.nodeTypes and self.currentSectionName == "Maps": #в a[0] должно храниться имя узла
#                    logging.info('Maps loading')
                    nodeType = self.nodeTypes[a[0]] #сохраняем тип узла, например compressor
                    methodName = f"get{nodeType}Map"
                    getattr(self, methodName)(a[0], initialData)
                if self.currentSectionName == "Rezults":
                    b = a[1].split(',', 1)
                    if len(b)==2:
                        b[0] = b[0].strip()
                        b[1] = b[1].strip()
                        initialData['Rezults'][a[0]]=[b[0],b[1]]                        
                    else:
                        initialData['Rezults'][a[0]]=[b[0],'']
                        
                    
            if self.currentSectionName == "Name":
                initialData['name'] = line
            if self.currentSectionName == "Scheme":
                a = line.split('-')
                for _a in a:
                    res = re.match(r"(\w+)\((\w+)\)", _a)
                    if DEBUG:
                        print(f"{res.group(2)} is {res.group(1)}")
                    self.nodeTypes[res.group(2)] = res.group(1)
                initialData["structure"] = self.nodeTypes

    def get(self, val):
        return self.preInitialData[val]

    def getCompressorMap(self, name, data):
        solverLog.info('Compressor map of '+name+': '+self.preInitialData[name])
        data[f"{name}.G_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "compressor")['G_function']
        data[f"{name}.PR_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "compressor")['PR_function']
        data[f"{name}.Eff_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "compressor")['Eff_function']

    def getTurbineMap(self, name, data):
        solverLog.info('Turbine map of '+name+': '+self.preInitialData[name])
        data[f"{name}.Capacity_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "turbine")['G_function']
        data[f"{name}.PR_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "turbine")['PR_function']
        data[f"{name}.Eff_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "turbine")['Eff_function']
        data[f"{name}.A_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "turbine")['Alfa_function']
        data[f"{name}.L_map"] = dev.import_map_function(os.getcwd()+'\\'+self.preInitialData[name], "turbine")['Lambda_function']

