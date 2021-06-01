# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 19:48:31 2019

@author: Sundukov

ГЛОБАЛЬНЫЕ TODO:
1+) сделать мониторинг невязок и варьируемых параметров
2+) расширить список параметров, которые могут определять режим работы двигателя - теперь можно задавать напрямую адрес любого параметра
3) сделать отображение режимной точки на графиках с характеристиками узлов (не совсем понятно как быть с тем, что характеристики узлов домножаются на поправки)
4+) вннести всю процедуру расчета внутрь класса engine
5) сделать так, чтобы посчитанный экземпляр engine сохранялся в роли результата предыдущей итерации и при необходимости из него можно было бы брать числа для текущей итерации
6) для переходных процессов нужно сохранять на каждой итерации экземпляр engine, а потом их извлекать в виде графиков
7+) нужно переделать класс Engine так, чтобы на основе данных пользовател яавтоматом генерировались нужные классы узлов и вся структура двигателя
8+) автоматизировать генерацию схемы, т.е. чтобы внутри методов __init__ и calculate не нужно было прописывать вручную порядок следования узлов. Схема двигателя должна задаваться польтзователем через файл
9) сгенерировать детальную эксель-таблицу с результатами
10) сделать варьируемую переменную расхода воздуха на входе в относительном виде, где 1 = расход на 100% при бетта = 0,5. Так будет удобнее на финальном графике с невязками
11) сделать возможность пользователю через файл описания модели добавлять расчет производных параметров, которые не вычисляются по умолчанию, чтобы потом их можно было например выводить в результатах
12) идея для парсера единиц измерения: он должен иметь две функции in('12unit/unit*unit^unit')=число_в_системем_СИ; out(число_в_СИ,'unit')='число_единицах_unit'
13) сделать вывод в лог перед расчетом полной распечатки всех исходных данных модели
14) в процессе решения невязок ввести проверку чтобывсе невязки и варьируемык переменные были вещественными числами
15) сделать так, чтобы в массиве исходные данных для расчета, там где пользователь задает режимный параметры, можно было задавать одновременно два параметра, например обороты ТК и температуру перед ТС и по результатам расчета модель использовала тот параметр, который бы обеспечивал непревышение обоих - это уже из боласти законов управления 
16)сейчас в конце класса engine есть костыль в виде общедвигательных параметров, а нужно чтобы пользователь задавал список нужных ему общедвигательных или любых других параметров через файл model.dat в разделе {Rezults}
17) сделать так, чтобы если расчет некорректный, то прога показывала в каком режиме проблема (если их несколько) и средний размер невязок
18)  в процессе расчета возможны ситуации, например, когда первоначальные  приближения криво заданы и модель сыпется в процессе расчета, нужно предусмотерть перехват исключений (подумать каких именно, вроде не всех подряд) метода calculate и соответственно автоматом попробовать подкрутить первоначальные приближения в нужную сторону
19)!!! для реактивных двигателей с количеством роторов более одного: в методе set_residuals_for_static_operating_mode есть такой потенциальный баг: сейчас он нормально работает, если считается либо одновальный ТРД (формируется одна невязка по мощности между компрессором и турбиной), либо не менее чем двухвальная установка со свободной турбиной (формируется невязка по мощности по всем роторам по отдельности кроме последнего)). В случае же например более чем двухвальной схемы ТРД у последнего ротора не будет невязки по последнему ротору - расчет будет крашиться! это надо исправить
20) !затестить, помоему была проблема если задать в файле input_data один из параметров без синтаксического сахара например turb.throttle.T (т.е. уровень вложенности больше 1го)
21) в методе equation_to_solve есть метод set_residuals_for_static_operating_mode. Сейчас он выполняется при каждой итерации, что нерационально, его достаточно выполнить один раз перед началом расчета, подумать как это сдлеать
22) подумать как устаканить механизм обновления увязочных коэффициентов ident_coefs, там в конце файла вообще свалка - разобрать! В том числе непонятный метод read_model(): и файл модели зачем-то задается через файл input_data и в коде, т.е. два раза - это не есть хорошо
23) нужно придумать какой-то метод, который бы извлекал из массива с исходными данными независимо от того что там задано (число или функция) функцию с методом calculate. В этой функции должна быть организована проверка, мол если пользователь не задал какое то число в файле модели, а проге оно обязательно, то она бы сообщала об этом в лог и говорила либо об ощ=шибке, либо что приняла такое-то значение по умолчанию
24)!!! разобраться с использованием поправок по Рейнольдсу, возможно нужно ввести какой-то переключатель того, использовать эти поправки или нет
25) сделать возможность задавать расход отбора функцией, а не только константой как сейчас
26) температура топлива должна задаваться ли боконстантой как сейчас, либо функцией, либо по умолчанию д.б. равна атмосферной
27) сделать переключатель в методке КС: чтобы химия считалась автоматом на основе таблиц НАСА, либо вручную по заданным свойствам L, теплотворной способности и и.т.
28) проверить возможный баг: если задать режим для тв7 перепадом на тк и приведенными оборотами - он хоть и не сходится, но считается, хотя вроде н едолжен, т.к. переопределен
29) сделать параметрик стади через человечейчий интерфейс
    
"""

import logging


solverLog=logging.getLogger('solverLog')
solverLog.propagate = False


import numpy as np
import pandas as pd
import copy
import sys
import os
import pathlib
import re
import datetime
from scipy.optimize import root 
#from scipy.optimize import fsolve
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

import Preloader as pl
import devices as dev
import thermodynamics as td
import Parser
#import thermodynamics_c_v1 as td

now = datetime.datetime.now()
date_text=now.strftime("date:%Y.%m.%d, time:%H:%M")

#logging.basicConfig(filename='info.log',filemode='w',level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
#solverLog=ThermoLog.setup_logger('solver_logger','info.log',logging.DEBUG)

#solverLog.info(date_text)

class Engine():
    def __init__(self,filename_of_input_data=''):
        
        self.time_before_init=datetime.datetime.now()
        self.time_before_start=np.nan
        
        #перечисление возможных единиц измерения
        self.units={'m':(1,0), 
           'mm':(0.001,0),
           'cm':(0.01,0),
           'dm':(0.1,0),
           'm':(1,0),
           'km':(1000,0),
           'ft':(0.3048,0),
           'in':(0.0254,0),
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
           'MN':(1000,0),
           'kgf':(9.80665,0),
           '':(1,0),
           '-':(1,0)}
        
        self.name_of_engine=''
        initial_data=dict() #словарь где будут храниться исходные данные
        
        initial_data['amount_of_rotors']=set()
        initial_data['amount_of_betta']=0
        self.residuals_statistics=pd.DataFrame()
        self.variables_statistics=pd.DataFrame()
        
        self.parameters_to_monitor=['turb.n_corr','compr.n_corr','compr.angle','compr.betta','turb.betta','Ne','compr.inlet.G','comb.outlet.T','compr.PRtt','compr.outlet.T','turb.throttle.T','turb.outlet.T'] #список параметров, которые хотим мониторить, пока что вводистя только так
        self.monitors=pd.DataFrame(columns=self.parameters_to_monitor) #тут будем храниить значеия тех переменных изменение которых хотим мониторить в процессе расчета

#        self.id_names=[] #в этой штуке будут храниться все узлы двигателя, каждый узел будет иметь свой собсвтенный id соответствующий порядковому номеру из этого списка. В конечном итоге все это нужно для быстродействия, чтобы не использовать строковые данные, только числовые
#        self.id_links=[]#в этой штук будут хранится ссылки на все узлы двигателя для возможности быстро к ним обратиться
        self.devices=dict()#словарь, где хранятся все узлы имя_узла = ссылка на объект узла
        self.named_main_devices=dict()#дополнительный вспомогательный словарь, в котором хранятся ссылки на некоторые ключевые узлы типа "первый компрессор", "последняя турбина" и т.п. - это нужно для удобства некоторых функций
        self.graphics_of_map={}
        
        self.arguments=dict()#словарь с необходимыми для расчета параметрами определяющими режим работы двигателя. Он формируется при создании экземпляра Engine каждым узлом, входящим в engine
        self.arguments0=dict()
        self.number_of_iterations=0
#        self.arguments_const=dict()
        self.residuals=dict()#словарь с необходимыми невязками () некотрые невязки формируются при инициализации узлов внутри метода инициализации этих узлов, а некоторые невязки формируются на уровне двигателя в зависимости от типа двигателя и типа задаваемых исходных данных
        self.balance_of_power_of_rotor=dict()#штука где будут храниться значения величин диасбалансов мощностей на кадом роторе
        self.user_input_operating_modes=list()#список, где будут храниться словари, каждый из которых определяет параметры режима работы двигателя, заданные пользователем
        self.operating_mode=dict()#список, где будут храниться параметры, определяющие режима работы двигателя, рассчитываемые в данный момент
        self.variables=dict() #количество переменных (а значит и невязок residuals) должно быть равно колво аргументов - колво аргументов заданных в исходных данных initial_data      
        self.initial_approaches=list()#список, где будут хранитсья первоначальные приближения, задаваемые пользоватлеем через input_data
        
        self.input_data_filename=''
        model_filename=self.read_filename_of_model(filename_of_input_data)
        Parser.Parser_formula.BASE_LINK_TO_EXTRACT = self
        pl.Preloader(model_filename, initial_data) #здесь идет предварительная обработка данных заданных пользователем через файл модели, не input_data!!!. Эти данные заносятся в массив initial_data, который подается на вход в initial_dat
        self.read_modes_from_input_data() #имя файла input_data передавать необязательно, но если оно передано, то у него наивысший приоритет - именно из него будут взяты данные, если не задано, то дальше будут проверяться параметры в строке при запуске через cmd, если и там пусто, то файла будет искать автоматически в рабочей директории - см.метод read_input_data
        # Parser.Parser_formula.BASE_LINK_TO_EXTRACT=self #задаем базовую ссылку на объект двигателя по которой нужно будет находить параметры в формулах

        self.rezults_data=initial_data['Rezults'] #здесь будут храниться данные о том, какие результаты выводить в конечный файл
        self.name_of_engine=initial_data['name']

        self.solvecontrol_use_variables_from_previus_iteration_as_first_estimate=True #штука, которая позволяет при ррасчете нескольких режимов использовать в качестве первоначальных приближений значения variables из предыдущего расчета
        
        self.ambient=dev.Ambient(initial_data,self)
        
        i = 0
        for name_of_device in initial_data["structure"]:
            if name_of_device=='in':
                solverLog.error(f'Error! Restricted name of device: {name_of_device}')
                raise SystemExit
            #инициализируем объект узла двигателя
            device = getattr(dev, initial_data["structure"][name_of_device])(initial_data, self.ambient if i == 0 else device, self, name=name_of_device)
            #задаем этот объект узла кка один из параметров объекта двигателя
            setattr(self, name_of_device, device)
            i += 1
 
        self.secondary_air_system=dev.Secondary_Air_System(initial_data,self,name='SAS')

        # for val in initial_data.values(): #в этом цикле проверяем, чтобы у всех объектов Parser.Parser_formula не было в параметрах строчных данных - они должны быть преобразованф в ссылки
        #     if isinstance(val,Parser.Parser_formula):
        #         val.check_undefined_parameters_and_udf_arguments()
        # for val in self.user_input_operating_modes: #в этом цикле проверяем, чтобы у всех объектов Parser.Parser_formula не было в параметрах строчных данных - они должны быть преобразованф в ссылки
        #     for val2 in val.values():
        #         if isinstance(val2,Parser.Parser_formula):
        #             val2.check_undefined_parameters_and_udf_arguments()
        # for val in Parser.Parser_formula.USER_DEFINED_FUNCTIONS.values():
        #     val.check_undefined_parameters_and_udf_arguments()

        for key in self.arguments.keys(): #ищем в массиве arguments количество роторов
            rez=re.findall(r'^n\d{1,3}$',key) #это шаблон для поиска обозначения вала
            if rez:
                self.balance_of_power_of_rotor[rez[0]]=0.0
        self.amount_of_rotors=len(initial_data['amount_of_rotors'])
        self.amount_of_betta=initial_data['amount_of_betta']
        
        self.prepare_input_data()
        
        #дальше временный костыль - нужно убрать, см.тудушку 16
        if self.name_of_engine=='TV7-117':
            self.Nsopla=np.nan#эквивалентная мощность сопла
            self.Nekv=np.nan#эквивалентная мощность двигателя
            self.Cekv=np.nan#эквивалентный удельный расход топлива
            self.Ce=np.nan
            self.PR=np.nan
        if self.name_of_engine=='GTE-170':
            self.Ne=np.nan
            # def _func(T):
            #     x_Th=[253.15,263.15,268.15,273.15,278.15,283.15,288.15,293.15,303.15,313.15]
            #     y_Tturb_out=[808.17,809.7,811.1,812.77,815.0,817.17,819.9,823.0,830.17,838.77]
            #     return np.poly1d(np.polyfit(x_Th,y_Tturb_out,2))
    # def law_of_Tout_turb_by_Th(self,T):
    #     x_Th=[253.15,263.15,268.15,273.15,278.15,283.15,288.15,293.15,303.15,313.15]
    #     y_Tturb_out=[808.17,809.7,811.1,812.77,815.0,817.17,819.9,823.0,830.17,838.77]
    #     return np.poly1d(np.polyfit(x_Th,y_Tturb_out,2))(T)

    def calculate(self):

        for name, device in self.devices.items():
            device.calculate(self)
        #дальше временный костыль - нужно убрать, см.тудушку 16
        if self.name_of_engine=='TV7-117':
            if np.round(self.ambient.external_conditions.V,4)>0:
                self.Nsopla=self.devices["outletLA"].outlet.Impulse*self.ambient.external_conditions.V/0.8 #КПД винта для расчета эквивалентной мощности принимаем равным 0,8 в соответствии с письмом с письмом от Зайналова 8.02.2019
            else:
                self.Nsopla=0.91*self.devices["outletLA"].outlet.Impulse*0.1019716/1.3596*1000 #формула из описания алгоритма мат модели ТВ7-117СТ
            self.Nekv=self.devices["pt"].N+self.Nsopla
            self.Cekv=(self.devices["cmbstr"].G_fuel*3600)/(self.Nekv/1000)
            self.Ce=(self.devices["cmbstr"].G_fuel)/(self.devices["pt"].N)
            self.PR=self.devices["lpc"].PRtt*self.devices["hpc"].PRtt
        if self.name_of_engine=='Jetcat':
            self.Thrust=self.devices["nozzle"].outlet.Impulse+(self.devices["nozzle"].outlet.Ps-self.devices['ambient'].external_conditions.Ps)*self.devices["nozzle"].outlet.F-self.devices['inlet'].inlet.G*self.devices['ambient'].external_conditions.V
            self.Cr=(self.devices["cmbstr"].G_fuel)/(self.Thrust)
        if self.name_of_engine=='GTE-170':
            self.Ne=self.turb.N+self.compr.N

    def read_filename_of_model(self,input_filename):
        # current_dir=os.getcwd()
        current_dir = pathlib.Path(__file__).parent.absolute()
        # files=os.listdir(current_dir)
        solverLog.info('Current working directory: ' + str(current_dir))
        solverLog.info('Searching input data...')
        if len(input_filename) > 0:  # если имя файла передано вручную через параметр input_filename
            solverLog.info('Using input data file from Python code')
            if os.path.exists(input_filename):  # тогда ищем файл по умолчанию
                self.input_data_filename = input_filename
                solverLog.info('Reading input data file: ' + input_filename)
            else:
                solverLog.error('ERROR: Not found input data file from Python code: ' + input_filename)
                raise SystemExit
        elif len(sys.argv) == 1:  # если в параметрах к файлу не переданы параметры, то попробуем найти файл сами в рабочей директории: для этого файл должен иметь формат .dat и внутри есбя иметь строку {model}
            solverLog.info('Finding input data file in working directory')
            files = os.listdir(current_dir)
            for file in files:
                if file.endswith(
                        '.dat') and 'model' not in file:  # тогда ищем файл в рабочей директории. У файла д.б. расширение dat и название не должно включать в себя слово "model"
                    with open(file) as _f:
                        for _line in _f:
                            # print(_line)
                            if ('{Model}' in _line) or ('{model}' in _line):
                                self.input_data_filename = file
                                solverLog.info('It was found input data file: ' + file)
                                _f.close()
                                break
                        if len(self.input_data_filename) > 0:
                            break
            if self.input_data_filename == '':
                solverLog.error('ERROR: Not found input data file in working directory')
                solverLog.info('Files in directory: ' + str(files))
                raise SystemExit

            # if os.path.exists('input_data.dat'):
            #     input_filename='input_data.dat'
            #     solverLog.info('Reading default file input_data.dat')
            # else:
            #     solverLog.error('ERROR: Not found default input_data.dat')
            #     raise SystemExit
        else:  # если в параметрах к файлу через командную строку передано чтото
            _temp = sys.argv[1].split('=')
            if _temp[0] == 'input':  # если передан параметр input, то в нем содржится имя файла с исходными данными
                self.input_data_filename = _temp[1]
                if not os.path.exists(self.input_data_filename):
                    solverLog.error('ERROR: Not found input data file ' + self.input_data_filename)
                    raise SystemExit
                else:
                    solverLog.info('Reading input data file ' + self.input_data_filename)

        with open(self.input_data_filename) as _file: #загоняем всю информацию из файла с исходными данными в словарь user_input
            calc_mode=False
            for line in _file: #перебираем по очереди все строки
                _temp=line.split('#') #если строка начинается с решетки, значит следом за ней комментарий, который мы отбрасываем
                if ('{model}' in _temp or '{Model}' in _temp) and calc_mode==False:
                    calc_mode = True
                    continue
                elif calc_mode==True:
                    _temp = re.findall(r'\s*(.+)\s*', _temp[0])[0]
                    if len(_temp)>0:
                        filename_of_model = _temp
                        solverLog.info('File of model: ' + filename_of_model)
                        break
        return filename_of_model

    def read_modes_from_input_data(self):#чтение из внешнего файла, задаваемого пользователем, данных о необходимых для расчета режимов. Обычно это файл input_data.dat
        user_input = {}
        with open(self.input_data_filename) as _file: #загоняем всю информацию из файла с исходными данными в словарь user_input
            calc_mode=''
            for_log_main=[]
            for line in _file: #перебираем по очереди все строки
                _temp=line.split('#') #если строка начинается с решетки, значит следом за ней комментарий, который мы отбрасываем
                _mode=re.match(r'\s*\{(.*)\}\s*',_temp[0])
                if _mode:
                    if _mode.group(1).strip()=='operating modes':
                        calc_mode='{operating modes}'
                        continue
                    else:
                        calc_mode=''
                if calc_mode=='{operating modes}':
                    #сначала извлекаем из строки раздел внутри круглых скобок, в них содержатся значения первоначальных приближений
                    _temp=re.findall(r'([^{}]+)(?:\{)*([^{}]+)(?:\{)*',_temp[0]) #в списке будут содержимое до скобок и второй элемент - содержимое внутри скобок
                    if not _temp:
                        continue

                    _initial_approach=re.findall(r'(?:\'|\")?(\w+)(?:\'|\")?\s*(?:=|:)\s*(\-?\d+\.?\d*)\s*',_temp[0][1])
                    # _parameters=re.findall(r'(\w+)\s*=\s*(\-?\d+\.?\d*)\s*([\w\%\/\*]*)',_temp[0][0]) #с помощью регулярок дербаним строку с параметрами режимов
                    # _parameters=re.findall(r'((?:(?:\w+\.{1})*\w+))\s*=\s*(\-?\d+\.?\d*)\s*([\w\%\/\*]*)',_temp[0][0]) #с помощью регулярок дербаним строку с параметрами режимов
                    _parameters=_temp[0][0].strip().split(';')
                    approach_dict=dict()
                    for approach in _initial_approach: #дербаним первоначальные приближения
                        name=approach[0]
                        value=float(approach[1])
                        approach_dict[name]=value                       
                    self.initial_approaches.append(approach_dict)

                    user_input=dict()
                    for_log=dict()
                    for _parameter in _parameters: #дербаним параметры задающие режим работы двигателя
                        if not _parameter:
                            continue
                        name,value=_parameter.strip().split('=',1)
                        if 'residual' in name:
                            name=name.strip()
                            _obj = Parser.Parser_formula()
                            _obj.prepare_RHS_of_formula(value.strip())
                            user_input[name] =_obj
                            for_log[name] = value.strip()
                        else:
                            rez=re.findall(r'([\d\.]+)(\w*)',value)[0]
                            self.unit_rezult=1
                            self.unit_operation='*'
                            value=float(rez[0])
                            unit=rez[1]
                            _temp=re.search(r'^\s*(?:C|С)\s*$',unit) #проверяем если исходные единицы измерения - градусы Цельсий, то это осбый случай (если  Цельсий стоит отдельно сам по себе это не то же самое, когда Цельсий находится в составе сложной единицы измерения с другими величинами)
                            if _temp:
                                user_input[name]=value*self.units[_temp.group(0)][0]+self.units[_temp.group(0)][1]
                            else:
                                self.parser_for_units(unit)
                                user_input[name]=value*self.unit_rezult
                            for_log[name]=rez[0]+rez[1]
                    self.user_input_operating_modes.append(user_input)
                    for_log_main.append(for_log)
                # if calc_mode=='{model_filename}' and re.findall(r'\s*(.*)\s*',_temp[0])[0]:
                #     _temp=re.findall(r'\s*(.*)\s*',_temp[0])[0] #с помощью регулярок дербаним строку
                #     if _temp!='':
                #         filename_of_model=_temp
                #         solverLog.info('File of model: '+filename_of_model)
                        
            solverLog.info('Reading input data: ok')
#        print(self.user_input_operating_modes)
        log_text='User inputs '+str(len(for_log_main))+' modes to solve:\n'
        for n,_string in enumerate(for_log_main):
            log_text+=str(n)+') '+str(_string)+'\n'
        solverLog.info(log_text)
        
        
#                    if calc_mode=='{identification}':  
#                
#                _parameters=re.findall(r'(\w+)\s*=\s*(\d+\.?\d*)\s*([\w\%\/\*]*)',data.group(2))#ищем в оставшесйя строке экспериментальные параметры
#                for parameter in _parameters:
#                    self.unit_rezult=1
#                    self.unit_operation='*'
#                    name=parameter[0]
#                    value=float(parameter[1])
#                    unit=parameter[2]
#                    _temp=re.search(r'^\s*(?:C|С)\s*$',unit) #проверяем если исходные единицы измерения - градусы Цельсий, то это осбый случай (если  Цельсий стоит отдельно сам по себе это не то же самое, когда Цельсий находится в составе сложной единицы измерения с другими величинами)
#                    if _temp:
#                        experiment_dict[name]=value*self.units[_temp.group(0)][0]+self.units[_temp.group(0)][1]
#                    else:
#                        self.parser_for_units(unit)
#                        experiment_dict[name]=value*self.unit_rezult
#                self.experiment_list.append(experiment_dict)
        
        
        
        
    
    def prepare_input_data(self): #преобразуем словарь user_input_operating_modes в нужный вид из вида, который зада пользователь
         #для удобства находим характерные узлы и всякие переменные и сохраняем их имена
        for name,device in self.devices.items(): #для удобства находим характерные узлы и всякие переменные и сохраняем их имена
            if device.__class__.__name__ == 'Turbine' and not('first_turbine' in self.named_main_devices):
#                self.named_main_devices['first_turbine_name']=name
#                self.named_main_devices['second_turbine_name']=name
#                self.named_main_devices['last_turbine_name']=name
                self.named_main_devices['first_turbine']=device
                self.named_main_devices['second_turbine']=device
                self.named_main_devices['last_turbine']=device
                self.named_main_devices['first_turbine_rotor']=str(device.rotor)
                self.named_main_devices['second_turbine_rotor']=str(device.rotor)
                self.named_main_devices['last_turbine_rotor']=str(device.rotor)
                continue
            if device.__class__.__name__ == 'Turbine' and ('first_turbine' in self.named_main_devices):
#                self.named_main_devices['second_turbine_name']=name
#                self.named_main_devices['last_turbine_name']=name
                self.named_main_devices['second_turbine']=device
                self.named_main_devices['last_turbine']=device
                self.named_main_devices['second_turbine_rotor']=str(device.rotor)
                self.named_main_devices['last_turbine_rotor']=str(device.rotor)
                continue
            if device.__class__.__name__ == 'Turbine' and ('first_turbine' in self.named_main_devices) and ('second_turbine' in self.named_main_devices):
#                self.named_main_devices['last_turbine_name']=name
                self.named_main_devices['last_turbine']=device
                self.named_main_devices['last_turbine_rotor']=str(device.rotor)
                continue
            if device.__class__.__name__ == 'Combustor' and not('combustor' in self.named_main_devices):
#                self.named_main_devices['combustor_name']=name
                self.named_main_devices['combustor']=device
                continue
            if device.__class__.__name__ == 'Compressor' and not('first_compressor' in self.named_main_devices):
#                self.named_main_devices['first_compressor_name']=name
#                self.named_main_devices['last_compressor_name']=name
                self.named_main_devices['first_compressor']=device
                self.named_main_devices['last_compressor']=device
                self.named_main_devices['first_compressor_rotor']=str(device.rotor)
                self.named_main_devices['last_compressor_rotor']=str(device.rotor)
                continue
            if device.__class__.__name__ == 'Compressor' and ('first_compressor' in self.named_main_devices):
#                self.named_main_devices['last_compressor_name']=name
                self.named_main_devices['last_compressor']=device
                self.named_main_devices['last_compressor_rotor']=str(device.rotor)
                continue
            if device.__class__.__name__ == 'Ambient':
#                self.named_main_devices['ambient_name']=name
                self.named_main_devices['ambient']=device
                continue
            if device.__class__.__name__ == 'Secondary_Air_System':
                self.named_main_devices['secondary_air_system']=device
                continue
        #в словаре ниже для удобства перечисляются типичные названия переменных, используемые в обиходе    
        possible_names={r'^ *(?:T|t)_*(?:h|atm) *$':'Th', #^-начстроки, пробел* - 0 или более пробелов, (:?T|t) - либо T либо t, _* - 0 или более вхождений _, (?:h|atm) - то же самое, пробел* - 0 или более пробелов, $ - конец строки
                        r'^ *(?:P|p)_*(?:h|atm) *$':'Ph',
                        r'^ *(?:dT|dt)_*(?:|ISA|isa) *$':'dT.ISA',
                        r'^ *(?:H|h) *$':'H',
                        r'^ *(?:M|Mp) *$':'M',
                        r'^ *(?:V|Vp) *$':'V',
                        r'^ *(?:Hum|fi|Humidity) *$':'Hum',
                        r'^ *n_*(?:1|tk|t|t1|tvd|TVD) *$':'n1',
                        r'^ *n_*(?:2|t2|tsd|TSD) *$':'n2',
                        r'^ *n_*(?:3|t3|tnd|TND) *$':'n3',
                        r'^ *n_*(?:st|ST|ts|TS) *$':('n'+self.named_main_devices['last_turbine_rotor']),
                        r'^ *n_*(?:pr|priv|corr|corrected)_*(?:1|k|k1|knd|ok) *$':(self.named_main_devices['first_compressor'].name+'.n_corr'),
                        r'^ *n_*(?:pr|priv|corr|corrected)_*(?:2|k2|kvd|ck) *$':(self.named_main_devices['last_compressor'].name+'.n_corr'),
                        r'^ *N_*(?:|e|v) *$':(self.named_main_devices['last_turbine'].name+'.N'),
                        r'^ *T_*(?:z|sa)_*(?:tk|t|tvd) *$':(self.named_main_devices['first_turbine'].name+'.throttle.T'),
                        r'^ *T41 *$':(self.named_main_devices['first_turbine'].name+'.throttle.T'),
                        r'^ *T_*(?:z|sa)_*(?:t2|tsd) *$':(self.named_main_devices['second_turbine'].name+'.throttle.T'),
                        r'^ *T_*(?:z|sa)_*(?:t3|tnd|ts|st) *$':(self.named_main_devices['last_turbine'].name+'.throttle.T'),
                        r'^ *T_*(?:|in)_*(?:t3|tnd|ts|st) *$':(self.named_main_devices['last_turbine'].name+'.input.T'),
                        r'^ *T_*out_*(?:t3|tnd|ts|st) *$':(self.named_main_devices['last_turbine'].name+'.output.T'),
                        r'^ *P_*(?:k1|knd|ok)_*(?:|out) *$':(self.named_main_devices['first_compressor'].name+'.output.P'),
                        r'^ *P_*(?:k|k2|kvd|ck)_*(?:|out) *$':(self.named_main_devices['last_compressor'].name+'.output.P'),
                        r'^ *(?:PR|Pi|PI)_*(?:k|k2|kvd|ck) *$':(self.named_main_devices['last_compressor'].name+'.PRtt'),
                        r'^ *(?:PR|Pi|PI)_*(?:k1|knd|ok) *$':(self.named_main_devices['first_compressor'].name+'.PRtt'),
                        r'^ *G_*(?:|in) *$':(self.named_main_devices['ambient'].name+'.outlet.G'),
                        r'^ *G_*(?:k1|knd|ok)_*(?:pr|rel|corr) *$':(self.named_main_devices['first_compressor'].name+'.input.G_corr')}
        #проверяем наличие в user_input_operating_mode типичные названия переменных и если находим, то заменяем их на нормальные имена

        for mode_num,user_input_operating_mode in enumerate(self.user_input_operating_modes):
            user_input_operating_mode_modified={}
            temp_unidentified_values=user_input_operating_mode.copy()
            keys=user_input_operating_mode.keys()
            for input_parameter_key in keys: #проходимся по всем ключам из словарей self.user_input_operating_modes 
                _value_found=False
                for pattern,new_key in possible_names.items(): #проходимся по всем ключам из словаря possible_names
                    # rez=re.findall(pattern,input_parameter_key)
                    if re.findall(pattern,input_parameter_key):
                        user_input_operating_mode_modified[new_key]=user_input_operating_mode[input_parameter_key]
                        temp_unidentified_values.pop(input_parameter_key)
    #                    self.user_input_operating_modes[new_key]=_temp
                        _value_found=True
                        break
                if self.str2parameter(input_parameter_key)!=str and _value_found==False:
                    user_input_operating_mode_modified[input_parameter_key]=user_input_operating_mode[input_parameter_key]
                    temp_unidentified_values.pop(input_parameter_key)  
            if len(temp_unidentified_values)>0: 
                solverLog.error('ERROR: Unidentified value(s) was found in input data. Mode #'+str(mode_num+1)+': '+str(temp_unidentified_values))
                print('ERROR: Unidentified value(s) was found in input data. Mode #'+str(mode_num+1)+': '+str(temp_unidentified_values))
                raise SystemExit
            #проверяем задал ли пользователь вместо температуры и давления высоту H и отклонение о стандартной температуры dT
            if ("Th" in user_input_operating_mode_modified) and ("dT.ISA" in user_input_operating_mode_modified):
                solverLog.error('ERROR: Переопределено значение температуры в исходных данных. Заданы одновременно Th и dT. Режим '+str(mode_num+1))    
                print('ERROR: Переопределено значение температуры в исходных данных. Заданы одновременно Th и dT. Режим '+str(mode_num+1))
                raise SystemExit
    
            if ("H" in user_input_operating_mode_modified) and ("Ph" in user_input_operating_mode_modified):
                solverLog.error('ERROR: Переопределено значение давления окружающей среды в исходных данных. Заданы одновременно H и Ph. Режим '+str(mode_num+1))    
                print('Переопределено значение давления окружающей среды в исходных данных. Заданы одновременно H и Ph. Режим '+str(mode_num+1))
                raise SystemExit
            if ("H" in user_input_operating_mode_modified) and ("Th" in user_input_operating_mode_modified):
                user_input_operating_mode_modified['Ph']=td.P_ISA(user_input_operating_mode_modified.pop('H'))
            elif ("H" in user_input_operating_mode_modified) and ("dT.ISA" in user_input_operating_mode_modified):
                user_input_operating_mode_modified['Ph']=td.P_ISA(user_input_operating_mode_modified['H'])
                user_input_operating_mode_modified['Th']=td.T_ISA(user_input_operating_mode_modified.pop('H'))+user_input_operating_mode_modified.pop('dT.ISA')

            self.user_input_operating_modes[mode_num]=user_input_operating_mode_modified

        log_text='Initial data for solving (SI):\n'
        for n,(_string1,_string2) in enumerate(zip(self.user_input_operating_modes,self.initial_approaches)):
            log_text+=str(n)+') '+str(_string1)+'. Initial approach: '+str(_string2)+'\n'
        solverLog.info(log_text)

        self.arguments0=copy.copy(self.arguments) #сохраняем исходный пустой словарь arguments, потом при расчете каждого отдельного режима будем его заполнять заново
        

    def prepare_arguments_and_variables(self): #штука, которая формирует массив arguments на основе operating_mode
        #проверяем наличие совпадений ключей в self.arguments и исходных данных self.user_input_operating_modes. При наличии совпадений заполняем соответствующий параметр в self.arguments
        self.arguments=copy.copy(self.arguments0) #сбрасываем значения в self.arguments
        
        for argument_key in self.arguments.keys():
            _temp=str() #используем как сигнализатор, что input_parameter_key совпал с одним из значений в self.arguments.keys
            for input_parameter_key in self.operating_mode.keys():
                if argument_key==input_parameter_key: #сначала проверяем не совпадает ли параметр из заданных пользователем с одним из параметров в arguments
                    if _temp != '':
                        solverLog.error('ERROR: Parameters are duplicated in the input data: {name1} and {name2} '.format(name1=_temp, name2=input_parameter_key))
                        raise SystemExit
                    _temp=input_parameter_key
                    self.arguments[argument_key]=self.operating_mode[input_parameter_key]
        
        #т.к. в arguments есть два ключа M и V, а нужно оставить только один из них, тот который задан, то далее убираем пустой ключ
        if not self.arguments['M'] is np.nan and self.arguments['V'] is np.nan:
            del self.arguments['V']
        elif not self.arguments['V'] is np.nan and self.arguments['M'] is np.nan:
            del self.arguments['M']
                        
                    
        #теперь формируем словарь с варьируемыми переменными путем выбрасывания из словаря self.arguments непустых значений
        
        for argument_key,argument_value in self.arguments.items():
            if argument_value is np.nan: 
                #здесь проверяем, если переменную можно брать из предыдущей итерации расчета, то берем
                if self.solvecontrol_use_variables_from_previus_iteration_as_first_estimate==False:
                    self.variables[argument_key]=np.nan
                else:
                    if argument_key not in self.variables:
                        self.variables[argument_key]=np.nan
            elif argument_key in self.variables:
                del self.variables[argument_key]
              
                
    #в этой штуке проверяем подряд все переменные в словаре self.variables и задаем первоначальные приближения        
    def estimate_variables(self,variables_estimates={}):  #variables_estimate - массив, получаемый от пользователя, где могут быть (не обязательно)  принудительно заданы первоначальные приближения, в случае их отсутствия приближения рассчитываются автоматически
        
        #по порядку перебираем все возможные значения переменных и назначаем им приближения
        #приоритетность использования первоначальных приближений: сначала задаваемые пользователем в файле input_data, затем из предыдущей итерации, затем автоматически
        for var_key,var_value in self.variables.items(): 
            if var_key in variables_estimates: #Сначала проверяем наличие в массиве variables_estimate
                self.variables[var_key]=variables_estimates[var_key]
            elif self.solvecontrol_use_variables_from_previus_iteration_as_first_estimate==True and not var_value is np.nan:
                continue
            elif re.findall(r'^n\d+$',var_key): #приближение по любым оборотам основных роторов. (чаще всего основные режимы лежат в диапазоне 0,9-1)
                self.variables[var_key]=0.95 #TODO! возможно стоит сделать так, чтобы рекомендуемые обороты лежали где-то по середине между минимальными и максимальнымии оборотами на характеристике компрессорау
            elif re.findall(r'^(.)*_*betta$',var_key): #приближение по параметру бетта для характеристик (обычно в диапазоне 0-1 в середине, если все работает как надо)
                self.variables[var_key]=0.5
            elif re.findall(r'^(.)*_*angle$',var_key): #приближение по параметру угла для характеристик, тут неочевидно TODO! возможно стоит пересмотреть алгоритм оценки альфа
                self.variables[var_key]=0.0
            elif re.findall(r'^(.)*_*Gf$',var_key): #приближение по параметру относительного расхода топлива. Величина может колебаться от 0 (нет топлива) до 1 (примерно стехиометрия). Обычно на двигателя средняя альфа в КС колеблется в диапазоне от 2-3 до 5-8. Возьмем среднюю 5, ей соответствует параметр = (1/альфа) = 0,2
                self.variables[var_key]=0.2                
        for var_key,var_value in self.variables.items():   #приближение по расходам сделано в отдельном цикле, потому что они могут зависеть от других приближений, задаваемых в предыдущем цикле выше       
            if re.findall(r'^Gin$',var_key):
                if var_key in variables_estimates: #Сначала проверяем наличие в массиве variables_estimate
                    self.variables[var_key]=variables_estimates[var_key]
                elif self.solvecontrol_use_variables_from_previus_iteration_as_first_estimate==True and not np.isnan(var_value):
                    continue
                else:#приближение по параметру расхода воздуха на входе в двигатель. Величина может колебаться в неограниченных пределах, можно примерно ее оценить из характеристики первого компрессора                 
                    name='n'+self.named_main_devices['first_compressor_rotor']
                    if name in self.variables:
                        _n_corr_temp=self.variables[name]
                    elif name in self.arguments and not np.isnan(self.arguments[name]):
                        _n_corr_temp=self.arguments[name]
                    
                    _betta_temp=self.variables[self.named_main_devices['first_compressor'].name+'.betta']

                    if hasattr(self.named_main_devices['first_compressor'],'angle'):
                        if self.named_main_devices['first_compressor'].name+'.angle' in self.variables:
                        # if hasattr(self.variables,self.named_main_devices['first_compressor'].name+'.angle'):
                            _angle_temp=self.variables[self.named_main_devices['first_compressor'].name+'.angle']
                        else:
                            _angle_temp = self.arguments[self.named_main_devices['first_compressor'].name + '.angle']
                        self.variables[var_key]=float(self.named_main_devices['first_compressor'].G_map(_n_corr_temp,_betta_temp,_angle_temp))

                    else:
                        self.variables[var_key]=float(self.named_main_devices['first_compressor'].G_map(_n_corr_temp,_betta_temp))
            elif re.findall(r'^Gref$',var_key): #приближение по параметру ссылочного расхода воздуха относительно которого задаются расходы охлаждающего воздуха
                if var_key in variables_estimates: #Сначала проверяем наличие в массиве variables_estimate
                    self.variables[var_key]=variables_estimates[var_key]
                elif self.solvecontrol_use_variables_from_previus_iteration_as_first_estimate==True and not var_value is np.nan:
                    continue
                else:
                    self.variables[var_key]=self.variables['Gin']
                
    #в этом методе дополняем массив невязок
    def set_residuals_for_static_operating_mode(self): 
        #так как мы считаем статический режим, то одна из невязок по умолчанию - это баланс мощности на всех роторах кроме последнего (подразумевается, что силовая турбина - это всегда последний по счету ротор, если иначе - нужно переделать алгоритм)
        # if self.amount_of_rotors>1: #эта ветвь работает когда у нас больше одного вала и последний из них - это вал силовой турбины, на него НЕ назначается невязка по мощности. Подразумевается, что этот последний вал генерит мощность на сторону
        #     for rotor in list(self.balance_of_power_of_rotor)[0:-1]:
        #         self.residuals['dN_'+rotor]=self.balance_of_power_of_rotor[rotor]/self.named_main_devices['first_turbine'].N #NB! здесь в знаменателе мощность первой турбины, что в общем не обязательно. Первая турбина выбрана, потому, что она есть всегда и обычно она самая мощная, относительно нее удобно переводить величины в относительный вид
        # else: #эта ветвь используется для одновального реактивного двигателя
        #     for rotor in list(self.balance_of_power_of_rotor):
        #         self.residuals['dN_'+rotor]=self.balance_of_power_of_rotor[rotor]/self.named_main_devices['first_turbine'].N #NB! здесь в знаменателе мощность первой турбины, что в общем не обязательно. Первая турбина выбрана, потому, что она есть всегда и обычно она самая мощная, относительно нее удобно переводить величины в относительный вид
        for rotor in list(self.balance_of_power_of_rotor):
            self.residuals['dN.'+rotor]=self.balance_of_power_of_rotor[rotor]/self.named_main_devices['first_turbine'].N #NB! здесь в знаменателе мощность первой турбины, что в общем не обязательно. Первая турбина выбрана, потому, что она есть всегда и обычно она самая мощная, относительно нее удобно переводить величины в относительный вид
            


        #далее просматриваем массив исходных данных заданных пользователем self.operating_mode и ищем там ключ(и), который задает еще одну невязку характеризующую режим работы двигателя (это ключ, который отсутствует в словаре self.arguments
        for key in self.operating_mode:
            if 'residual' in key:
                self.residuals[key]=self.operating_mode[key].calculate()
            elif key not in self.arguments:
                if self.operating_mode[key]==0:
                    solverLog.error('Ошибка!!! параметр {parameter} равен нулю, а относительного него считается неявзка - это фиаско, братан! По идее таких параметров не должно быть. Обращайтесь к разработчику'.format(parameter=self.operating_mode[key]))
                if self.named_main_devices['last_turbine'].name+'.N'==key:
                    _rotor=self.named_main_devices['last_turbine'].name_of_n
                    _N=self.operating_mode[key]
                    self.residuals['dN.'+_rotor]=(self.balance_of_power_of_rotor[_rotor]-_N)/self.named_main_devices['first_turbine'].N
                else:
                    self.residuals[key]=(self.operating_mode[key] - self.str2parameter(key) )/self.operating_mode[key]

                
        
#        self.named_main_devices['last_turbine_rotor']
        
    
    #формируем функцию, которую удобно скормить scipy.optimize.root, чтобы она ее решила
    def equation_to_solve(self,variables_list):
        for var_key,var_val in zip(self.variables.keys(),variables_list):
#            print(var_key, var_val)
            self.variables[var_key]=var_val
        
        self.arguments.update(self.variables)
        not_calculated_model=copy.deepcopy(self)
        Parser.Parser_formula.BASE_LINK_TO_EXTRACT=not_calculated_model
        try:
            not_calculated_model.calculate()
        except:
            print("TROUBLE in calculating of model :( ")
#        print(self.lpc.N)
#        print(self.hpc.N)
#        print(self.hpt.N)
        not_calculated_model.set_residuals_for_static_operating_mode() #TODO! есть баг: после успешного расчета когда зеначения варьируемых параметров уже известны и проводится контрольный расчет с этими варьируемыми параметрами на основе базовой "чистой"/исходной модели, то внутрь этой "чистой" модели не попадают те невязки в массив residuals, которые рассчитываются  вэтой функции. Возможное решение - внести эту функцию внутрь calculate
        if len(self.variables)!=len(not_calculated_model.residuals):
            solverLog.warning(f'Warning: lenght of variables array not equivalent to residuals array: \n Variables:{self.variables} \n Residuals: {not_calculated_model.residuals}')
            # raise SystemExit
        self.monitors=self.monitors.append(not_calculated_model.extract_values_for_monitors(),ignore_index=True)
        self.residuals_statistics=self.residuals_statistics.append(not_calculated_model.residuals,ignore_index=True)
        self.variables_statistics=self.variables_statistics.append(self.variables,ignore_index=True)
#        print(not_calculated_model.residuals)
        self.number_of_iterations+=1
#        print(self.number_of_iterations)
        return list(not_calculated_model.residuals.values())
    
#        здесь нужно сформировать массив невязок отталкиваясь от заданного пользователем массива input_data и добавить их в частично сформированный массив residuals

    def extract_values_for_monitors(self): #штука для записи мониторируемых параметров в массив self.monitors
        _temp={}
        for parameter in self.parameters_to_monitor:
            val=self.str2parameter(parameter)
            _temp[parameter]=val
        return _temp
        
        
    def str2parameter(self,string): #вспомогательная функция для преобразования строки, содержащей ссылку на параметр, собственно в значение этого параметра
        broken_string = string.split('.')
        rez=self
        for val in broken_string:
            if hasattr(rez,val):
                rez=getattr(rez,val)
            else:
                return 'unknown parameter '+string
        return rez          
    
    
    def solve_modes(self): #решение для стаицонарного режима работы двигателя
        # solverLog.info('Initializating...')
#        self.read_input_data()
#        self.prepare_input_data() #тут формируем список self.user_input_operating_modes, в котором каждый элемент - это словарь с параметрами, определяющими режим работы двигателя
        rezults=list() #здесь будут хранитсья результаты расчета, т.е. экземпляоы класса Engine с посчитанными режимами
        # solverLog.info('Initializating: ok')
        self.time_before_start=datetime.datetime.now()
        solverLog.info('Solving...')
        entire_status=[] #будем тут хранить среднюю величину невязок по всем расчетным режимам
#        quantity_of_modes=len(self.user_input_operating_modes) #определяем количество режимов которые надо посчитать и по очереди их считаем
#        self.arguments0=copy.copy(self.arguments) #сохраняем исходный пустой словарь arguments, потом при расчете каждого отдельного режима будем его заполнять заново
        for number_of_mode,self.operating_mode in enumerate(self.user_input_operating_modes): 
            solverLog.info('Mode '+str(number_of_mode)+str(': start of solving...'))
            self.time_before_mode_start=datetime.datetime.now()
            self.prepare_arguments_and_variables() #тут заполняем словарь arguments и формируем словарь variables (но пока не заполняем)
            self.estimate_variables(self.initial_approaches[number_of_mode])#тут заполняем словарь variables первоначальными переменными
            solverLog.info('Initial variables: '+str(self.variables))
            solverLog.info('Initial arguments: '+str(self.arguments))
            for key,val in self.variables.items():
                if np.isnan(val):
                    solverLog.error(f'Error: undefined variable "{key}" in variables array: {self.variables}')
                    raise SystemExit
            stability_factor=100 #значение 100 указано по умолчанию в описании функции root scipy https://docs.scipy.org/doc/scipy/reference/optimize.root-lm.html#optimize-root-lm уменьшение значение увеличивает время расчета, но делает расчет более стабильным!
            variables0=copy.copy(self.variables)
            while stability_factor>0.01: #если продолжит что-то разваливаться, то возможно стоит уменьшить значение слева
                try:
                    rez=root(self.equation_to_solve,list(self.variables.values()),method='lm',options={'ftol': 1.0e-10, 'xtol': 1.0e-10, 'factor': stability_factor})
                    break
                except ValueError:
                    solverLog.info('Unstable calculation. Trying to reduce parameter "factor" in function scipy.optimize.root. Factor = '+str(stability_factor))
                    stability_factor/=4
                    self.variables=copy.copy(variables0)
            if stability_factor<=0.01:
                solverLog.error('Error! Variables: '+str(self.variables))
                self.make_graphics()
                raise SystemExit
            
            dtime=datetime.datetime.now()-self.time_before_mode_start
            solverLog.info('Rezulting variables: '+str(self.variables))
            solverLog.info('Rezulting residuals: '+str(dict(self.residuals_statistics.iloc[-1])))
            solverLog.info('Mode '+str(number_of_mode)+': completed. (time:'+str(dtime)+'). Solver success status:'+str(rez['success'])+'. '+str(rez['message']+'\n'))

            entire_status.append(self.residuals_statistics.iloc[-1].sum())
            model_to_save_rezults=copy.deepcopy(self) #создаем копию текущей еще не посчитанной модели, чтобы на следующем шаге посчитать ее и не "пачкать" текущую модель
            model_to_save_rezults.calculate()#полученную модель нужно воспринимать как результат расчета, хранящий в себе результата расчета текущей модели
            model_to_save_rezults.set_residuals_for_static_operating_mode()
            rezults.append(model_to_save_rezults)
#            print(rez['fun'])
#            print(rez['qtf'])
#        self=copy.deepcopy(model_to_save_rezults)#последний расчет сохраняем в текущий объект
        if all(val<0.00001 for val in entire_status):
            solverLog.info('Solving status: Full success')
#            print('Solving status: Full success')
        else:
            solverLog.info('Solving status: !!!warning!!! Check sum of residuals by modes:') 
            solverLog.info(str(entire_status))
        time_of_init=self.time_before_start-self.time_before_init
        time_of_calc=datetime.datetime.now()-self.time_before_start
        solverLog.info("Time of initialization: "+str(time_of_init))
        solverLog.info("Time of solving: "+str(time_of_calc))
#        print("Time of solving: "+str(time_of_calc))
        return rezults
    
    def make_graphics(self):
        fig_residuals, axes = plt.subplots()
        fig_residuals.set_size_inches(15, 15)
        fig_variables, axes2 = plt.subplots()
        fig_variables.set_size_inches(15, 15)
        # fig_monitors, axes3 = plt.subplots()
        # fig_monitors.set_size_inches(15, 15)
        
        indexes=list(self.residuals_statistics.index.values)
        for column_caption in self.residuals_statistics.columns.values.tolist():
            axes.plot(indexes,list(self.residuals_statistics[column_caption]),label=column_caption)
        axes.legend(fontsize=12)
        axes.set_xlabel('Number of iteration',fontsize=12)
        axes.set_ylabel('Residual',fontsize=12)
        axes.set_title('Monitor of residuals',fontsize=16)
        
        for column_caption in self.variables_statistics.columns.values.tolist():
            axes2.plot(indexes,list(self.variables_statistics[column_caption]),label=column_caption)
        axes2.legend(fontsize=12)
        axes2.set_xlabel('Number of iteration',fontsize=12)
        axes2.set_ylabel('Variable',fontsize=12)
        axes2.set_title('Monitors of variable parameters',fontsize=16)
        
        for column_caption in self.monitors.columns.values.tolist():
            fig_monitors, axes3 = plt.subplots()
            fig_monitors.set_size_inches(15, 15)
            axes3.plot(indexes,list(self.monitors[column_caption]),label=column_caption+'='+str(self.monitors[column_caption].iloc[-1]))
            axes3.legend(fontsize=12)
            axes3.set_xlabel('Number of iteration',fontsize=12)
            axes3.set_ylabel('Variable',fontsize=12)
            axes3.set_title('Monitors of user defined parameters',fontsize=16)
            plt.close(fig_monitors)
            fig_monitors.savefig('monitor['+column_caption+'].png',bbox_inches='tight')
            
        plt.close(fig_residuals)
        plt.close(fig_variables)
        # plt.close(fig_monitors)
        fig_residuals.savefig('residuals.png',bbox_inches='tight')
        fig_variables.savefig('variables.png',bbox_inches='tight')
        # fig_monitors.savefig('monitors.png',bbox_inches='tight')
        
    def make_graphics_of_maps(self,rezults): #TODO! переделать так, чтобы могла работать если характеристика зависит еще от угла ВНА
        # fig_residuals, axes = plt.subplots()
        # fig_residuals.set_size_inches(15, 15)
        names_of_maps=['first_compressor','last_compressor','first_turbine','second_turbine','last_turbine']
        color_map = plt.get_cmap('coolwarm')
        for name in names_of_maps:
            if name in self.named_main_devices:
                if 'compressor' in name:
                    if ('first_compressor' in name) or ('last_compressor' in name and not(self.named_main_devices['last_compressor'] is self.named_main_devices['first_compressor'])):
                        fig, axes = plt.subplots()
                        fig.set_size_inches(20, 20)
                        axes.set_xlabel('G, кг/с',fontsize=15)
                        axes.set_ylabel('PR',fontsize=15)
                        axes.set_title('Характеристика компрессора. Название узла: {name}'.format(name=self.named_main_devices[name].name),fontsize=15)
                        self.graphics_of_map[name]=axes
                        G_map=self.named_main_devices[name].G_map
                        PR_map=self.named_main_devices[name].PR_map
                        Eff_map=self.named_main_devices[name].Eff_map
                        n_min=G_map.get_knots()[0][0]*10
                        _n_min2=np.ceil(n_min)
                        n_max=G_map.get_knots()[0][-1]*10
                        _n_max2=np.floor(n_max)
                        betta_min=-0.2
                        betta_max=1.2
                        n_vector=[n_min/10]+np.arange(_n_min2/10, _n_max2/10, 0.01).tolist()+[n_max/10]
                        n_vector=[x/self.named_main_devices[name].ident_n_value for x in n_vector]
                        n_vector_hq=np.linspace(n_min/10, n_max/10, num=200)
                        n_vector_hq=[x/self.named_main_devices[name].ident_n_value for x in n_vector_hq]
                        betta_vector=np.arange(betta_min, betta_max, 0.1)
                        betta_vector_hq=np.linspace(betta_min, betta_max, num=200)
                        n_colors = [color_map(i) for i in np.linspace(0, 1, len(n_vector))]
                        betta_colors = [color_map(i) for i in np.linspace(0, 1, len(betta_vector))]
                        for ni_color in zip(n_vector,n_colors):
                            ni=ni_color[0]
                            ncolor=ni_color[1]
                            Gvect=[]
                            PRvect=[]
                            # Effvect=[]
                            for bettai in betta_vector_hq:
                                Gvect.append(float(G_map(ni,bettai)*self.named_main_devices[name].ident_G_value))
                                PRvect.append(float(PR_map(ni,bettai)*self.named_main_devices[name].ident_PR_value))
                                # Effvect.append(float(Eff_map(ni,bettai)))
                            axes.plot(Gvect,PRvect,color=ncolor,linewidth=1.2,linestyle='dotted')
                            axes.text(Gvect[0]-0.01,PRvect[0]+0.03,np.round(ni,3),fontsize=10)
                        for bettai_color in zip(betta_vector,betta_colors):
                            bettai=bettai_color[0]
                            bettacolor=bettai_color[1]
                            Gvect=[]
                            PRvect=[]
                            # Effvect=[]
                            for ni in n_vector_hq:                        
                                Gvect.append(float(G_map(ni,bettai)*self.named_main_devices[name].ident_G_value))
                                PRvect.append(float(PR_map(ni,bettai)*self.named_main_devices[name].ident_PR_value))
                                # Effvect.append(float(Eff_map(ni,bettai)))
                            axes.plot(Gvect,PRvect,color=bettacolor,linewidth=1.2,linestyle='dotted')
                            axes.text(Gvect[-1],PRvect[-1]+0.03,np.round(bettai,3),fontsize=10)
                        PR_contour=PR_map(n_vector_hq,betta_vector_hq)*self.named_main_devices[name].ident_PR_value
                        G_contour=G_map(n_vector_hq,betta_vector_hq)*self.named_main_devices[name].ident_G_value
                        Eff_contour=Eff_map(n_vector_hq,betta_vector_hq)*self.named_main_devices[name].ident_Eff_value
                        eff_max=np.ceil(max(Eff_map.get_coeffs()*self.named_main_devices[name].ident_Eff_value)*100)
                        lev_up=np.linspace((eff_max-3)/100,eff_max/100,7).tolist()
                        lev_mid=np.linspace((eff_max-10)/100,(eff_max-3)/100,8)[0:-1].tolist()
                        lev_down=np.linspace(0,(eff_max-10)/100,10)[0:-1].tolist()
                        lev=lev_down+lev_mid+lev_up
                        axes.contourf(G_contour,PR_contour,Eff_contour,levels=lev,cmap='jet')
                        _axes=axes.contour(G_contour,PR_contour,Eff_contour,levels=lev,colors='black',linewidths=0.5)
                        axes.clabel(_axes, inline=1, fontsize=8,colors='k')
                        axes.grid()
                        X=[]
                        Y=[]
                        for rez in rezults:
                            X.append(rez.named_main_devices[name].inlet.G_corr)
                            Y.append(rez.named_main_devices[name].PRtt)
                            axes.scatter(X,Y,color='black',s=50,marker='+')
                        axes.set_xlim([4,10])
                        axes.set_ylim([3,20])
                            
                if 'turbine' in name:
                    if ('first_turbine' in name) or ('second_turbine' in name and not(self.named_main_devices['second_turbine'] is self.named_main_devices['first_turbine'])) or ('last_turbine' in name and not(self.named_main_devices['last_turbine'] is self.named_main_devices['second_turbine'])):
                        fig, axes = plt.subplots()
                        fig.set_size_inches(20, 20)
                        axes.set_xlabel('G*Т^0.5/P*n, кг/с*К^0.5/кПа',fontsize=15)
                        axes.set_ylabel('PR',fontsize=15)
                        axes.set_title('Характеристика турбины. Название узла: {name}'.format(name=self.named_main_devices[name].name),fontsize=15)
                        self.graphics_of_map[name]=axes
                        Cap_map=self.named_main_devices[name].Cap_map
                        PR_map=self.named_main_devices[name].PR_map
                        Eff_map=self.named_main_devices[name].Eff_map
                        n_min=Cap_map.get_knots()[0][0]*10
                        _n_min2=np.ceil(n_min)
                        n_max=Cap_map.get_knots()[0][-1]*10
                        _n_max2=np.floor(n_max)
                        betta_min=-0.2
                        betta_max=1.2
                        n_vector=[n_min/10]+np.arange(_n_min2/10, _n_max2/10, 0.05).tolist()+[n_max/10]
                        n_vector_hq=np.linspace(n_min/10, n_max/10, num=200)
                        betta_vector=np.arange(betta_min, betta_max, 0.1)
                        betta_vector_hq=np.linspace(betta_min, betta_max, num=20)
                        n_colors = [color_map(i) for i in np.linspace(0, 1, len(n_vector))]
                        betta_colors = [color_map(i) for i in np.linspace(0, 1, len(betta_vector))]
                        for ni_color in zip(n_vector,n_colors):
                            ni=ni_color[0]
                            ncolor=ni_color[1]
                            Capvect=[]
                            PRvect=[]
                            # Effvect=[]
                            for bettai in betta_vector_hq:
                                Capvect.append(float(Cap_map(ni,bettai)*ni))
                                PRvect.append(float(PR_map(ni,bettai)))
                                # Effvect.append(float(Eff_map(ni,bettai)))
                            Capvect=np.array([val for val in Capvect])
                            axes.plot(Capvect,PRvect,color=ncolor,linewidth=1.2,linestyle='dotted')
                            axes.text(Capvect[-1],PRvect[-1]+0.03,np.round(ni,2),fontsize=10)
                        for bettai_color in zip(betta_vector,betta_colors):
                            bettai=bettai_color[0]
                            bettacolor=bettai_color[1]
                            Capvect=[]
                            PRvect=[]
                            # Effvect=[]
                            for ni in n_vector_hq:                        
                                Capvect.append(float(Cap_map(ni,bettai)*ni))
                                PRvect.append(float(PR_map(ni,bettai)))
                                # Effvect.append(float(Eff_map(ni,bettai)))
                            Capvect=np.array([val for val in Capvect])
                            axes.plot(Capvect,PRvect,color=bettacolor,linewidth=1.2,linestyle='dotted')
                            axes.text(Capvect[-1],PRvect[-1],np.round(bettai,2),fontsize=10)
                        PR_contour=PR_map(n_vector_hq,betta_vector_hq)
                        Cap_contour=Cap_map(n_vector_hq,betta_vector_hq)*n_vector_hq[:,np.newaxis]
                        Eff_contour=Eff_map(n_vector_hq,betta_vector_hq)
                        if self.name_of_engine=='Jetcat': #TODO! костыльь
                            eff_max=86
                        else:
                            eff_max=np.ceil(max(Eff_map.get_coeffs())*100)
                        lev_up=np.linspace((eff_max-3)/100,eff_max/100,7).tolist()
                        lev_mid=np.linspace((eff_max-10)/100,(eff_max-3)/100,8)[0:-1].tolist()
                        lev_down=np.linspace(0,(eff_max-10)/100,10)[0:-1].tolist()
                        lev=lev_down+lev_mid+lev_up
                        axes.contourf(Cap_contour,PR_contour,Eff_contour,levels=lev,cmap='jet')
                        _axes=axes.contour(Cap_contour,PR_contour,Eff_contour,levels=lev,colors='black',linewidths=0.5)
                        axes.clabel(_axes, inline=1, fontsize=8,colors='k')
                        axes.grid()
                        X=[]
                        Y=[]
                        for rez in rezults:
                            X.append(rez.named_main_devices[name].throttle.capacity*rez.named_main_devices[name].n_corr)
                            Y.append(rez.named_main_devices[name].PRtt)
                            axes.scatter(X,Y,color='black',s=50,marker='+')
        plt.show()


    def parser_for_units(self,unit_string): #штука, которой на вход передают строку, содержащую единицы измерения (допускается наличие символов *,/,^), которые она парсит и переводит эту строку в числовое значение, соответствующее переводу единиц измерения в СИ
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
            if  self.unit_operation=='*':
                self.unit_rezult*=unit_rez
            elif self.unit_operation=='/':
                self.unit_rezult/=unit_rez
                
    #метод для замены указанных увязочных коэффициентов в модели (используется для увязки)
    def update_ident_coefs(self,new_ident_coefs):
        for coef_name,coef_value in new_ident_coefs.items(): #пробегаемся по всем коэффициентам
            _parameter=coef_name.split('.')
            if _parameter[0]!='ident':
                solverLog.error('ERROR: Incorrect identification coefficient: '+coef_name)
                raise SystemExit
            if _parameter[1]=='SAS':
                self.devices['SAS'].ident_G[int(_parameter[2])]=coef_value
                continue
            elif _parameter[1] in self.devices:
                if hasattr(self.devices[_parameter[1]],'ident_'+_parameter[2]+'_value'):
                    setattr(self.devices[_parameter[1]],'ident_'+_parameter[2]+'_value',coef_value)
                    continue
                else:
                    solverLog.error('ERROR: Not found parameter from identification coefficient: '+coef_name)
#                print('ERROR: Not found device from identification coefficient: '+coef_name)
                    raise SystemExit
            else:
                solverLog.error('ERROR: Not found device from identification coefficient: '+coef_name)
#                print('ERROR: Not found device from identification coefficient: '+coef_name)
                raise SystemExit
     
    #функция для записи в dataframe результатов расчета в виде, который переваривает бенч
    def data_to_table(self,Name='',Value='',Dimension='',round_to=4):
        if self.df.empty:
            ind=0
        else:
            ind=self.df.index[-1]+1
        self.df.loc[ind]=[Name,Dimension,round(float(Value),round_to)]
        
    def data_to_table2(self,Name='',Value='',Dimension='',round_to=6): #nоже самое, только value - это список
        list_of_values=[]
        for val in Value:
            list_of_values.append(round(float(val),round_to))
        if self.df.empty:
            ind=0
        else:
            ind=self.df.index[-1]+1
        self.df.loc[ind]=[Name,Dimension]+list_of_values
    
    #штука для сохранения результатов в файл на основе данных, переденных через раздел {Rezults} в файле модели. Результаты извлекаются из объекта results, передаваемого через конструктор - это должен быть экземпляр engine
    def save_rezults_to_file(self,rezults_data=np.nan,filename_where_to_save=''): 
        if isinstance(rezults_data, Engine):     
            if not hasattr(self,'df'):
                self.df = pd.DataFrame(columns=['Name','Dimension','Value'])
            for rezult_data in self.rezults_data:
                p = Parser.Parser(rezults_data)
                p.parse(self.rezults_data[rezult_data][0])
                val=p.calculate()
                self.data_to_table(Name=rezult_data,Value=val,Dimension=self.rezults_data[rezult_data][1])
            self.df.to_csv(filename_where_to_save)
        elif isinstance(rezults_data, list):
            names_of_modes=[]
            for i in np.arange(1,len(rezults_data)+1):
                names_of_modes.append('mode '+str(i))
            if not hasattr(self,'df'):
                columns=['Name','Dimension']
                columns=columns+names_of_modes
                self.df = pd.DataFrame(columns=columns)
            for name,formula_and_dimension in self.rezults_data.items():
                _name=name
                _dimension=formula_and_dimension[1]
                _formula=formula_and_dimension[0] #TODO!!! ввести проверку на то, что формула вычисляема! иначе прога вылетает, а в логах не пишется почему
                _values=[]
                for rezult in rezults_data:
                    p = Parser.Parser(rezult)
                    p.parse(_formula)
                    val=p.calculate()
                    _values.append(val)
                self.data_to_table2(Name=_name,Value=_values,Dimension=_dimension)
            self.df.to_csv(filename_where_to_save)

                
            
            
            
    def parametric_study(self,par1_dict,par2_dict):
        parametric_study_rezults=[]
        par1_name=list(par1_dict.keys())[0]
        par1_val_list=list(par1_dict.values())[0]
        par2_name=list(par2_dict.keys())[0]
        par2_val_list=list(par2_dict.values())[0]
        for par1_val in par1_val_list:
            self.update_str_parameter(par1_name,par1_val)
            for par2_val in par2_val_list:
                self.update_str_parameter(par2_name,par2_val)
                solverLog.info(f'PARAMETRIC_STUDY: {par1_name}={par1_val}; {par2_name}={par2_val}')
                _rez=self.solve_modes()
                parametric_study_rezults.append({par1_name:par1_val,par2_name:par2_val,'rez':_rez})
        return parametric_study_rezults
                    

                        
            
    def update_str_parameter(self,string,new_val): #вспомогательная функция, которой на вход подается строка с именем параметра, который нужно заменить в модели
        broken_string = string.split('.')
        rez=self
        for val in broken_string:
            if hasattr(rez,val):
                _rez=getattr(rez,val)
                if isinstance(_rez,float) or isinstance(_rez,int):
                    setattr(rez,val,new_val)
                else:
                    if val is broken_string[-1]:
                        solverLog.error('ERROR! Wrong parameter: '+string)
                        raise SystemExit
                    else:
                        rez=_rez
            elif 'ident' in val:
                _device=broken_string[1]
                if 'SAS' in _device:
                    self.devices['SAS'].ident_G[int(broken_string[2])]=new_val
                    break
                else:
                    _parameter=broken_string[2]
                    setattr(getattr(rez,_device),_parameter,new_val) 
            else:
                solverLog.error('ERROR! Wrong parameter: '+string)
                raise SystemExit

           
        
#ДАЛЬШЕ ЗАПУСК! Надо бы вынести в отдельный пусковой файл. При увязке отключить
#ВЕРСИЯ ДЛЯ ПК    
# Model0=Engine('input_data_for_identification.dat') #исходная непосчитанная модель с заведенными в нее исходными данными
#ВЕРСИЯ ДЛЯ ЗАПУСКА ЧЕРЕЗ КОМАНДНУЮ СТРОКУ
#Model0=Engine(read_model()) #исходная непосчитанная модель с заведенными в нее исходными данными

# Model0.update_ident_coefs(ident_coefs)
# rezults=Model0.solve_modes()
# Model0.save_rezults_to_file(rezults_data=rezults[-1],filename_where_to_save='test.csv')
# Model0.make_graphics()
# Model0.make_graphics_of_maps()

# solverLog.info('Writing rezults: ok')


#solverLog.shutdown()
