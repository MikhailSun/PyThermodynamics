# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 12:59:31 2019

@author: Sundukov
глобальные TODO!!!
1)сделать штуку, которой на вход говоришь посмотреть влияние какого-либо параметра на другие параметры и диапазон изменения этого 1го параметра, штука строит график
2)только для увязки: сделать штуку, которая посчитав один режим из имеющихся записывает в файл исходных данных в массив где задаются расчетные режимы строку с первоначальными приближениями - это позволит сократить время на увязку, т.к. эти приближения не всегда есть от пользователя
"""
import pandas as pd
import Engine as eng
import re
import logging
import numpy as np
import scipy.optimize as opt
import random as rnd
from matplotlib import pyplot as plt
#import tkinter as tk
import ThermoLog
import copy

#identLog=ThermoLog.setup_logger('identification_logger','ident.log',logging.DEBUG)
#identLog.propagate = False

ThermoLog.setup_logger('identLog', 'identification.log',logging.DEBUG,stream=True)
identLog=logging.getLogger('identLog')
identLog.propagate = False
solverLog=logging.getLogger('solverLog')




#Увязка модели по режимам
class identification():
    def __init__(self,filename=''): #приинициализации сразу задаем модель расчетную
#    def __init__(self): #приинициализации сразу задаем модель расчетную
        identLog.info('IDENT: Start of identification...')
        self.title=''
        self.model=eng.Engine(filename)
        self.experiment_list=[] #штука где будут храниться словари с параметрами экспериментальных режимов
        self.rezults_list=[] #здесь будет храниться список с результатами расчетных режимов
        self.errors={} #здесь будут хранитсья величины невяязок между экспериментальными и расчетными параметрами
        self.errors_statistics=pd.DataFrame()
        self.ident_coefs_statistics=pd.DataFrame()
        self.influence_dict={} #здесь будем хранить коэффициенты влияния
        self.units={'m':(1,0), #перечисление возможных единиц измерения
                   'mm':(0.001,0),
                   'cm':(0.01,0),
                   'dm':(0.1,0),
                   'km':(1000,0),
                   'Pa':(1,0),
                   'kPa':(1000,0),
                   'MPa':(1000000,0),
                   'gr':(0.001,0),
                   'g':(0.001,0),
                   'kg':(1,0),
                   't':(1000,0),
                   's':(1,0),
                   'sec':(1,0),
                   'min':(60,0),
                   'h':(3600,0),
                   'hr':(3600,0),
                   'C':(1,273.15),
                   'С':(1,273.15), #кириллицей
                   'K':(1,0),
                   'rev':(2*np.pi,0),
                   'ob':(2*np.pi,0),
                   '1':(2*np.pi,0),
                   'W':(1,0),
                   'kW':(1000,0),
                   'MW':(1000000,0),
                   'hp':(735.49875,0), #метрическая лошадиная сила
                   'hp_mechanical':(745.69987158227022,0), #британская/механическая лошадиная сила (ее используют у нас редко, но возможно использование в Британии, США, Канаде...)
                   '%':(0.01,0),
                   'N':(1,0),
                   'kN':(1000,0),
                   'MN':(1000000,0),
                   'kgf':(9.80665,0),
                   '':(1,0)}
        
        if len(filename)==0:
            filename=self.model.input_data_filename #это на тот случай, если файл не задан явно, то пробуем найти его сами через модуль Engine
        self.read_experimental_data(filename) #TODO! временный костыль, здесь экспериментальные данные берутся из этого файла, но по факту, нужно указывать откуда
        #TODO!!! сделать через файл user_input пользователь должен сформировать словарь, где именам параметров из массива исходных данных {identification} соответствуют ссылки в модели. По этим ссылкам будут рассчитываться параметры, по которым будет проводиться увязка TODO! попробовать сделать автоматом создание этих ссылок
        #TODO! добавить веса для каждого из параметров и для каждого из режимов
        #TODO! подумать как сделать так, чтобы можно было менять значение знаменателя в формуле вычисления относительной ошибки. Знаменателем должен быть возможный предполагаемый диапазон изменения вычисляемого параметра
        
        self.ident_links={} #тут хранятся ссылки между названиями параметров, которые задал пользователь и соответствующими названиями в модели
        self.reasonable_range_of_variation={} #тут соответствующие диапазоны изменения параметров от минимума до максимума, эти диапазоны подставляются в знаменатель формулы вычисления относительной ошибки, т.е. это что-то вроде весового коэффициента при оценке общего отклонения всех расчетных параметров от экспериментальных
        self.read_identification_links_and_diapasons(filename) #эта штука заполняет два массива выше

        # self.ident_links={
        #               'Thrust':'Thrust',
        #               'tk':'compr.outlet.T',
        #               'Pk':'compr.outlet.P',
        #               'Tt':'turb.outlet.T',
        #               'Pt':'turb.outlet.P',
        #               'Gt':'cmbstr.G_fuel',
        #               'G':'inlet.inlet.G'
        #               }    
        #в этом словаре хранятся допустимые диапазоны изменения параметров в единицах СИ (от малого газа до максимального режима), эти диапазоны будут подставляться в знаменатель формулы вычисления ошибки
        # self.reasonable_range_of_variation={
        #               'Thrust':250,
        #               'tk':150,
        #               'Pk':200,
        #               'Tt':150,
        #               'Pt':50,
        #               'Gt':0.004,
        #               'G':0.4
        #               }  
        
        #словарь, где перечисляются увязочные коэффициенты, которыми можно варьировать для увязки, в кортеже(увязочный коэффициент (его первоначальное приближение), его пределы мин/макс-если есть) TODO! сделать так, чтобы пользователь задавал это через файл
#         self.ident_coefs={'ident.SAS.1':1.0 ,
#                          # 'ident.SAS.2':1.2,
#                          # 'ident.SAS.3':1.3,
#                         # 'ident.SAS.4':1.0,
#                         # 'ident.inlet.sigma':1.0,
#                         # 'ident.compr.G':1.0,
#                         'ident.compr.PR':1.0,
#                         'ident.compr.Eff':1.0,
# #                        'ident.lpc.n':1.0,
#                         # 'ident.hpc.G':1.0,
#                         # 'ident.hpc.PR':1.0,
#                         # 'ident.hpc.Eff':1.0,
# #                        'ident.hpc.n':1.0,
#                         'ident.cmbstr.sigma':1.0,
#                         'ident.cmbstr.Eff':1.0,
#                         'ident.turb.Cap':1.0,
#                         # 'ident.turb.PR':1.0,
#                         'ident.turb.Eff':1.0,
# #                        'ident.hpt.n':1.0,
# #                        'ident.hpt.A':1.0,
# #                        'ident.hpt.L':1.0,
#                         'ident.turb.Eff_mech':1.0,
#                         # 'ident.pt.Cap':1.0,
# #                        'ident.pt.PR':1.0,
#                         # 'ident.pt.Eff':1.0,
# #                        'ident.pt.n':1.0,
# #                        'ident.pt.A':1.0,
# #                        'ident.pt.L':1.0,
#                         # 'ident.pt.Eff_mech':1.0,
#                         'ident.nozzle.sigma':1.0}
        # self.bounds=[(0.5,1.5),(0.97,1.03),(0.95,1.01),(0.95,1.01),(0.95,1.01),(0.99,1.01),(0.90,1.01),(0.98,1.02),(0.95,1.02)]
        self.ident_coefs={}
        self.bounds=[]
        self.read_identification_coefficients_and_bounds(filename)

    def read_identification_coefficients_and_bounds(self,filename): #штука для считывания ссылок связывающих наименования параметров из файла с расчетными параметрами
    #удобный сайт для проверки регулярок https://regex101.com/
        experiment_filename=open(filename)
        calc_mode=''
        for line in experiment_filename: #перебираем по очереди все строки
            ident_links_dict={}#
            _main_text=line.split('#') #если строка начинается с решетки, значит следом за ней комментарий, который мы отбрасываем
            _mode=re.match(r'\s*\{(.*)\}\s*',_main_text[0])
            if _mode:
                if _mode.group(1).strip()=='identification-coefficients-bounds':
                    calc_mode='identification-coefficients-bounds'
                else:
                    calc_mode=''
                    
            if calc_mode=='identification-coefficients-bounds':
                if not '=' in  _main_text[0]:
                    continue
                _temp=_main_text[0].split('=')
                ident_coef=_temp[0] #имя коэффициента участвующего в увязке
                _temp=_temp[1].split(';')
                ident_val=float(_temp[0]) #исходное значение коэффициента участвующего в увязке
                self.ident_coefs[ident_coef]=ident_val
                
                _temp=_temp[1].split('-')
                low_bound=float(_temp[0])
                high_bound=float(_temp[1])
                self.bounds.append((low_bound,high_bound))
        experiment_filename.close()


    def read_identification_links_and_diapasons(self,filename): #штука для считывания ссылок связывающих наименования параметров из файла с расчетными параметрами
    #удобный сайт для проверки регулярок https://regex101.com/
        experiment_filename=open(filename)
        calc_mode=''
        for line in experiment_filename: #перебираем по очереди все строки
            ident_links_dict={}#
            _main_text=line.split('#') #если строка начинается с решетки, значит следом за ней комментарий, который мы отбрасываем
            _mode=re.match(r'\s*\{(.*)\}\s*',_main_text[0])
            if _mode:
                if _mode.group(1).strip()=='identification-links-diapason':
                    calc_mode='{identification-links-diapason}'
                else:
                    calc_mode=''
                    
            if calc_mode=='{identification-links-diapason}':
                if not '=' in  _main_text[0]:
                    continue
                _temp=_main_text[0].split('=')
                experiment_parameter_name=_temp[0]
                _temp=_temp[1].split(';')
                model_name=_temp[0]
                diapason=_temp[1]
                
                self.ident_links[experiment_parameter_name]=model_name
                self.unit_rezult=1
                self.unit_operation='*'
                _temp=re.findall(r'\s*(\d+\.?\d*)\s*([\w\%\/\*\^]*)',diapason)#ищем в оставшесйя строке диапазона числовое значение и размерность
                self.parser_for_units(_temp[0][1])
                diapason=float(_temp[0][0])*self.unit_rezult
                self.reasonable_range_of_variation[experiment_parameter_name]=diapason
        experiment_filename.close()

    
    def parser_for_units(self,unit_string): #штука, которой на вход передают строку, содержащую единицы измерения (допускается наличие символов *,/,^), которые она парсит и переводит эту строку в числовое значение, соответствующее переводу единиц измерения в СИ
        #результат сохраняется в self.unit_rezult
        #парсер работает в связке с двумя внешними переменными, которые перед первым обращением к парсеру должны быть равны self.unit_rezult=1 и  self.unit_operation='*'
        #TODO! проверить работает ли знак вычисления степени ^
        _rez=re.search(r'(?:\/|\*)',unit_string) #
        if _rez:#ищем с втроке / или *
            operation=_rez.group(0)
            _str_start=unit_string[0:_rez.start()]
            _str_end=unit_string[_rez.end():]
            #далее работаем с началом строки, ищем в ней знак степени
            _rez=re.search(r'([a-zA-Z]+)\^(\d+\.*\d*)',_str_start)
            if _rez:  #ищем указатель степени, если нашли, то применяем
                unit_rez=self.units[_rez.group(1)][0]**float(_rez.group(2))
            else:
                unit_rez=self.units[_str_start][0]
            #далее вычисляем промежуточное значение
            if  self.unit_operation=='*':
                self.unit_rezult*=unit_rez
            elif self.unit_operation=='/':
                self.unit_rezult/=unit_rez
            self.unit_operation=operation
            self.parser_for_units(_str_end)
        else: #если не нашли в строке / или *
            _rez=re.search(r'([a-zA-Z]+)\^(\d+\.*\d*)',unit_string)
            if _rez:  #ищем указатель степени
                unit_rez=self.units[_rez.group(1)][0]**float(_rez.group(2))
            else:
                unit_rez=self.units[unit_string][0]
            #далее вычисляем промежуточное значение
            if self.unit_operation=='*':
                self.unit_rezult*=unit_rez
            elif self.unit_operation=='/':
                self.unit_rezult/=unit_rez       
    
    def read_experimental_data(self,filename):
        #удобный сайт для проверки регулярок https://regex101.com/
        experiment_filename=open(filename)
        calc_mode=''
        for line in experiment_filename: #перебираем по очереди все строки
            experiment_dict={}#
            _main_text=line.split('#') #если строка начинается с решетки, значит следом за ней комментарий, который мы отбрасываем
            _mode=re.match(r'\s*\{(.*)\}\s*',_main_text[0])
            if _mode:
                if _mode.group(1).strip()=='identification':
                    calc_mode='{identification}'
                else:
                    calc_mode=''
                    
            if calc_mode=='{identification}':  
                data_name=re.match(r'^\s*(name\s*=\s*){1}(.*)$',_main_text[0]) #ищем имя увязки, если задано
                if data_name and 'name' in data_name.group(1):
                    self.title=data_name.group(2)
                    continue
                data=re.match(r'(^\s*[0-9_./]*[a-zA-Zа-яА-Я]+[0-9_/]*)(.*)',_main_text[0]) #с помощью регулярок дербаним строку с экспериментальными данными, находим название режима
                if data and '=' not in data.group(1): #сначала определяем название режима
                    experiment_dict['name']=data.group(1)
                else:
                    continue
                
                _parameters=re.findall(r'(\w+)\s*=\s*(\d+\.?\d*)\s*([\w\%\/\*\^]*)',data.group(2))#ищем в оставшесйя строке экспериментальные параметры
                for parameter in _parameters:
                    self.unit_rezult=1
                    self.unit_operation='*'
                    name=parameter[0]
                    value=float(parameter[1])
                    unit=parameter[2]
                    _temp=re.search(r'^\s*(?:C|С)\s*$',unit) #проверяем если исходные единицы измерения - градусы Цельсий, то это осбый случай (если  Цельсий стоит отдельно сам по себе это не то же самое, когда Цельсий находится в составе сложной единицы измерения с другими величинами)
                    if _temp:
                        experiment_dict[name]=value*self.units[_temp.group(0)][0]+self.units[_temp.group(0)][1]
                    else:
                        self.parser_for_units(unit)
                        experiment_dict[name]=value*self.unit_rezult
                self.experiment_list.append(experiment_dict)
        experiment_filename.close()
    
    def str2parameter(self,rezult,string): #вспомогательная функция для преобразования строки, содержащей ссылку на параметр, собственно в значение этого параметра
        broken_string = string.split('.')
        rez=rezult
        for val in broken_string:
            rez=getattr(rez,val)
        return rez  
                
    #формирует сложный словарь, где перечисляются все отклонения эксперимента от расчета
    def compare_experimental_and_calculated_parameters(self,rezult_list=[]):
        if not rezult_list:
            rezult_list=self.rezults_list
        if len(self.experiment_list)!=len(rezult_list):
            identLog.error('IDENT: ERROR: Unequal amount of experimental and calculated modes!')
            raise SystemExit
        self.errors.clear()
        _sum_error_value=0
        _n_modes=0
        for comparing_rezults in zip(self.experiment_list,rezult_list): #проходимся по рассчитанным и экспериментальным режимам
            exp_mode,calc_mode=comparing_rezults
            #расчет ошибки:
            mode_name=exp_mode['name']
            _errors={}
            _mode_error_value=0 #величина среднего отклонения расчета от эксперимента для одного режима
            _n_parameters_in_mode=0
            for exp_key,exp_value in exp_mode.items():#проходимся по всем параметрам в режиме
                if exp_key=='name':
                    continue
                else:
                    calc_value=self.str2parameter(calc_mode,self.ident_links[exp_key])
                    _delta=calc_value-exp_value
                    _error_value=_delta/exp_value
                    _errors[exp_key]=[_error_value,exp_value,calc_value,_delta,(_delta)/exp_value*100] #элемент словарья _errors хранит в себе список [относительная ошибка,эксп знач,расч знач,абс отклонение, относит отклонение в процентах]
                    _mode_error_value+=_error_value**2
                    _n_parameters_in_mode+=1
                    
            _mode_error_value=(_mode_error_value/_n_parameters_in_mode)**0.5
            _errors['mid_error']=_mode_error_value
            _n_modes+=1
            _sum_error_value+=_mode_error_value**2
            self.errors[mode_name]=_errors  #этот словарь хранит в качесьве элементов словари _errors (см.выше) для каждого из режимов
        _sum_error_value=(_sum_error_value/_n_modes)**0.5
        self.errors['mid_error']=_sum_error_value
        
    #функция, которую нужно минимизировать для увязки. В качестве аргумента передается список, содержащий увязочные коэффициенты, т.е. value[0] из словаря self.ident_coefs
    def function_to_minimize(self,variables_list):
        for coef_key,coef_value in zip(self.ident_coefs,variables_list):
            self.ident_coefs[coef_key]=coef_value
        self.model.update_ident_coefs(self.ident_coefs)      
        solverLog.info(str(self.ident_coefs))
        self.rezults_list=self.model.solve_modes()
        self.compare_experimental_and_calculated_parameters()
        
        return self.errors['mid_error']
    
    def callback(self,variables):
#        print('CALLBACK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        self.ident_coefs_statistics=self.ident_coefs_statistics.append(self.ident_coefs,ignore_index=True)
        _errors={}
        for mode in self.errors:
            if mode!='mid_error':
                _errors[mode]= self.errors[mode]['mid_error']
            else:
                _errors[mode]=self.errors['mid_error']
        _temp1=str(copy.copy(self.ident_coefs))
        _temp2=str(copy.copy(_errors))
        identLog.info('IDENT: ident_coefs: '+_temp1)
        identLog.info('IDENT: errors: '+_temp2)
        
#        identLog.info('variables: '+str(variables))


        self.errors_statistics=self.errors_statistics.append(_errors,ignore_index=True)
        self.make_graphics()
        print(str(variables))
        
    def make_graphics(self):
        fig_ident_coefs, axes = plt.subplots()
        fig_ident_coefs.set_size_inches(15, 15)
        fig_errors, axes2 = plt.subplots()
        fig_errors.set_size_inches(15, 15)
        
        indexes=list(self.ident_coefs_statistics.index.values)
        for column_caption in self.ident_coefs_statistics.columns.values.tolist():
            axes.plot(indexes,list(self.ident_coefs_statistics[column_caption]),label=column_caption)
        axes.legend(fontsize=12)
        axes.set_xlabel('Number of iteration',fontsize=12)
        axes.set_ylabel('Ident coef',fontsize=12)
        axes.set_title('Identification coefficients. '+self.title,fontsize=16)
        
        for column_caption in self.errors_statistics.columns.values.tolist():
            axes2.plot(indexes,list(self.errors_statistics[column_caption]),label=column_caption)
        axes2.legend(fontsize=12)
        axes2.set_xlabel('Number of iteration',fontsize=12)
        axes2.set_ylabel('Error',fontsize=12)
        axes2.set_title('Errors. '+self.title,fontsize=16)
        plt.close(fig_ident_coefs)
        plt.close(fig_errors)
        fig_ident_coefs.savefig('ident_coefs.png',bbox_inches='tight')
        fig_errors.savefig('ident_errors.png',bbox_inches='tight')

    def calculate_influence(self):
        
        self.model.update_ident_coefs(self.ident_coefs)      
        self.rezults_list=self.model.solve_modes()
        self.compare_experimental_and_calculated_parameters()
        _rez0={}
        for key in self.errors:
            if 'mid_error' not in key:
                _rez0[key]=self.errors[key]['mid_error']
            else:
                _rez0['mid_error']=self.errors['mid_error']
        
        for coef,value in self.ident_coefs.items():
            _arg0=value
            _arg1=1.01*value
            # self.ident_coefs[coef]=_arg1
            self.model.update_ident_coefs({coef:_arg1})      
            self.rezults_list=self.model.solve_modes()
            self.compare_experimental_and_calculated_parameters()
            _rez1={}
            for key in self.errors:
                if 'mid_error' not in key:
                    _rez1[key]=self.errors[key]['mid_error']
                else:
                    _rez1['mid_error']=self.errors['mid_error']
            _infl={}
            for rez0_key,rez1_key in zip(_rez0,_rez1):
                if rez0_key != rez1_key:
                    print('Error in calculating influence coefficients!')
                    raise SystemExit
                _infl[rez0_key]=((_rez1[rez1_key]-_rez0[rez0_key])/(_arg1-_arg0))
            # print('!!!!!!!!!!!!!!!!!!!')
            # print(_infl)
            self.influence_dict[coef]=_infl
            # self.ident_coefs[coef]=_arg0
            self.model.update_ident_coefs({coef:_arg0})
            print('Influence coefficients: '+coef)
            print('rez0='+str(_rez0))
            print('rez1='+str(_rez1))
            print('arg0='+str(_arg0))
            print('arg1='+str(_arg1))
            print('inf='+str(_infl))
            
          
    #метод осуществляющий увязку            
    def identificate(self):
        x0=np.array(list(self.ident_coefs.values()))
#        self.rezults_list=self.model.solve_modes()
#        self.compare_experimental_and_calculated_parameters()
#        self.ident_coefs_statistics=self.ident_coefs_statistics.append(self.ident_coefs,ignore_index=True)
#        _errors={}
#        for mode in self.errors:
#            if mode!='mid_error':
#                _errors[mode]= mode[mode]['mid_error']
#            else:
#                _errors[mode]=mode['mid_error']

#        self.errors_statistics=self.errors_statistics.append(_errors,ignore_index=True)
        self.rezults_list=self.model.solve_modes()
        self.compare_experimental_and_calculated_parameters()
        identLog.info('IDENT: State before identification:')
        self.callback(self.ident_coefs.values())
        identLog.info('IDENT: ^^^State before identification^^^')
#        opt_rez=opt.minimize(self.function_to_minimize,x0,bounds=self.bounds,options={'maxiter':30,'disp':True,'eps': 1e-4,'gtol': 1e-05},callback=self.callback)
#        opt_rez=opt.differential_evolution(self.function_to_minimize, bounds=self.bounds, strategy='best1bin', maxiter=1000, popsize=15, tol=0.01, mutation=(0.5, 1), recombination=0.7, seed=None, callback=self.callback, disp=True, polish=True, init='latinhypercube', atol=0, updating='immediate', workers=1)
        opt_rez=opt.minimize(self.function_to_minimize, x0, method='TNC', bounds=self.bounds, callback=self.callback, options={'eps': 1e-04, 'scale': None, 'offset': None, 'mesg_num': None, 'maxCGit': -1, 'maxiter': 100, 'eta': -1, 'stepmx': 0, 'accuracy': 0, 'minfev': 0, 'ftol': -1, 'xtol': -1, 'gtol': -1, 'rescale': -1, 'disp': True})
#        opt_rez=opt.basinhopping(self.function_to_minimize, x0, niter=100)
        self.opt_rez=opt_rez
        return opt_rez
        
    #TODO!!! поэкспериментировать с настройками решателя и методами
    #!!!TODO сделать для увязки вывод лога в отдельный файл: результаты невязок self.errors_statistics и self.errors - текущие, величины увязочных коэффициентов self.ident_coefs_statistics и self.ident_coefs - текущие, отклонения, обновление графиков после каждой итерации
    
    
    
"""
eps - шаг варьирования, который используется  в начале алгоритма минимизации при "прощупывании" увязочных коэффициентов
"""           


#window = tk.Tk('Test')


# A=identification('input_data_for_identification.dat')   

#ident_coefs= {'ident.SAS.1': 1.0023940355823906, 'ident.SAS.2': 1.2062941333188681, 'ident.SAS.3': 1.2, 'ident.SAS.4': 1.0005251529054515, 'ident.inlet.sigma': 0.9861521215841195, 'ident.lpc.PR': 0.9899992729298865, 'ident.lpc.Eff': 1.005, 'ident.hpc.PR': 0.96, 'ident.hpc.Eff': 1.005, 'ident.cmbstr.sigma': 1.01, 'ident.cmbstr.eff': 1.0, 'ident.hpt.Cap': 1.063529198765094, 'ident.hpt.Eff': 1.01, 'ident.hpt.Eff_mech': 1.005, 'ident.pt.Cap': 0.9868865995631785, 'ident.pt.Eff': 1.01, 'ident.pt.Eff_mech': 1.005, 'ident.outlet.sigma': 1.0101}
# A.model.update_ident_coefs(ident_coefs)
# A.rezults_list=A.model.solve_modes()
# A.compare_experimental_and_calculated_parameters()

# A.identificate()
# A.make_graphics()


#test=[]
#
#while len(test)<30:
#    test.append(rnd.gauss(1,0.00000000000000000002))
#    
#print(test)
#test2=A.function_to_minimize(test)
#print(test2)

#A.rezults_list=A.model.solve_modes()
#A.compare_experimental_and_calculated_parameters() 
#
#
#!!!сгенерить function_to_minimize()
#
#optrez=opt.minimize(function_to_minimize, x0, args=(), method=None, jac=None, hess=None, hessp=None, bounds=None, constraints=(), tol=None, callback=None, options=None)


#сначала массив с экспериментальными данными
#создаем dataframe, где будут храниться экспериментальные данные
#experiment = pd.DataFrame(columns=['Operating mode','Nv pr','tg pr','ntk pr','nts','Ce pr','Gt pr','PR'])
##df.index.name="#"
#
##функция для записи в dataframe
#def data_to_table(df,**val):
#    if df.empty:
#        ind=0
#    else:
#        ind=df.index[-1]+1
#    df.loc[ind]=[Name,round(float(Value),round_to),Target,Condition,Dimension,Description,Comments,''