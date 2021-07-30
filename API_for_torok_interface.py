import sys
import pandas as pd

import Parser
import devices as dev
import Engine as eng
import thermodynamics as td
import makecharts as gr
import numpy as np



parameters_to_filter=['name','was_edited','name_of_parent','upstream','devices','_link_to_Gref','bleed_expansion','air_bleed_out','air_bleed_in','ambient.outlet','outlet_ideal'] #отфильтровываем ненужные названия параметровесли точно знаем как они должны называться
parameters_to_filter2=['name','ident','Gref','mass_comp','error'] #аналогично, если знаем часть название параметров, т.е. ключевые слова по которым фильтруем в названия параметров
def filter_value(val):
    if val in parameters_to_filter:
        return True
    for filter_item in parameters_to_filter2:
        if filter_item in val:
            return True

if len(sys.argv)>1:
    params = sys.argv
    command = params[1]
    parameters = params[2:]
    # if len(params)<3:
    #     command=params[1]
    # else:
    #     parameters=params[2]
else:
    print("No command to execute")

if command=='get_compressor_input_parameters':
    print(command)
    df=pd.DataFrame(dev.Compressor.input_parameters)
    print(df)
    df.to_json('data_for_torok/input_parameters.json',force_ascii=False)
elif command=='get_channel_input_parameters':
    print(command)
    df=pd.DataFrame(dev.Channel.input_parameters)
    print(df)
    df.to_json('data_for_torok/input_parameters.json',force_ascii=False)
elif command == 'get_turbine_input_parameters':
    print(command)
    df=pd.DataFrame(dev.Turbine.input_parameters)
    print(df)
    df.to_json('data_for_torok/input_parameters.json',force_ascii=False)
elif command == 'get_combustor_input_parameters':
    print(command)
    df=pd.DataFrame(dev.Combustor.input_parameters)
    print(df)
    df.to_json('data_for_torok/input_parameters.json',force_ascii=False)
elif command == 'get_convergentnozzle_input_parameters':
    print(command)
    df=pd.DataFrame(dev.ConvergentNozzle.input_parameters)
    print(df)
    df.to_json('data_for_torok/input_parameters.json',force_ascii=False)
elif command == 'get_list_of_possible_parameters': #эта штука генерит текстовый файл с деревом всех возможных параметров, которые может задавать пользователь
    print(command)
    name_of_file='list_of_possible_parameters.txt'
    print(f'Parameters saved to file {name_of_file}')
    Model = eng.Engine(filename_of_input_data='input_data_GTE170.dat',only_check=False)

    tree=[]

    to_filter=False
    for dev_name, dev_link in Model.devices.items(): #проходимся по всем узлам
        for par_name, par_link in dev_link.__dict__.items():
            if filter_value(par_name):
                continue
            text1=dev_name+'.'+par_name
            if filter_value(text1):
                continue
            if isinstance(par_link,Parser.Parser_formula):
                continue
            if isinstance(par_link,td.CrossSection):
                for par_name2, par_link2 in par_link.__dict__.items():
                    if filter_value(par_name2):
                        continue
                    text2=text1+'.'+par_name2
                    tree.append(text2)
            else:
                tree.append(text1)

    with open(name_of_file, 'w') as f:
        for item in tree:
            f.write(f"{item}\n")

elif command == 'calculate_formula':
    print(command)
    print(parameters)#['f(x,y)=x+y #,kfhvlkerh', '1,2', '3,4']

    data_obj=Parser.data()
    formula_obj=Parser.Parser_formula(link_to_extract=data_obj)

    formula = parameters[0].split('#')
    formula = formula[0].strip()

    formula_obj.prepare_formula(formula)
    keys_list=list(formula_obj.ARGUMENTS.keys())

    args = dict()
    values_list=list()
    #цикд до конца листа
    for i in parameters[1:]:
        #values=i.split(',')
        values_list.append(i.split(','))
        #print(values_list)

    outfile = open('data_for_torok/results_formula.dat', 'w')

    for i in range(len(values_list)):
        for key,value in zip(keys_list,values_list[i]):
            args[key]=float(value)
        #print(args)
        formula_obj.insert_values_in_arguments(**args)
        res=formula_obj.calculate()
        outfile.write(str(res))
        outfile.write('\n')
        #print(res)

    outfile.close()
    #results_formula.dat

elif command == 'print_plot':
    print(command)
    print(parameters)

    data_obj=Parser.data()
    formula_obj=Parser.Parser_formula(link_to_extract=data_obj)

    formula = parameters[0].split('#')
    formula = formula[0].strip()

    formula_obj.prepare_formula(formula)

    #1 точка - нет графика
    #2 и больше - 1 условие - 1 ргумент(x,y) - если больше писать шо незя
    #              2 - берем мин и макс и в интервале Х и У - это границы графика
    #python api.py print_plot 'f(x)=x+1' 1 2

    keys_list = list(formula_obj.ARGUMENTS.keys())
    if len(keys_list)>1:
        print('Количество аргументов больше одного. Построение графика невозможно')
        outfile = open('data_for_torok/results_formula.dat', 'w')
        outfile.write('Количество аргументов больше одного. Построение графика невозможно')
        outfile.close()

    elif len(parameters[1:]) == 1:
        print('Количество данных точек недостаточно для определения диапазона')
        outfile = open('data_for_torok/results_formula.dat', 'w')
        outfile.write('Количество данных точек недостаточно для определения диапазона')
        outfile.close()

    elif len(parameters) < 4:
        print('Неверное количество параметров')
        outfile = open('data_for_torok/results_formula.dat', 'w')
        outfile.write('Неверное количество параметров')
        outfile.close()

    else:
        values_list = []
        # цикд до конца листа
        values_list=[float(val) for val in parameters[1:3]]

        args = dict()
        x = []
        y = []
        X_min = np.min(values_list)
        X_max = np.max(values_list)

        n_of_points = int(parameters[3])
        #n_of_points = 10
        for j in range(n_of_points+1):
            X_current = (X_max - X_min)*(j)/n_of_points + X_min
            args[keys_list[0]] = X_current
            formula_obj.insert_values_in_arguments(**args)
            Y_current = formula_obj.calculate()
            x = np.append(x,X_current)
            y = np.append(y,Y_current)

        print(x,y)



        # Fig = gr.Chart(points_for_scatter=[{'x':x,'y':y}],
        #                points_for_plot=[{'x': x, 'y': y}], title=parameters[0], xlabel='X', ylabel='Y',
        #                dpi=150, figure_size=(10, 10))
        # Fig.figure.savefig('data_for_torok/plot')
        Fig = gr.Chart(points_for_scatter=[{'x':x,'y':y,'s':50,'c':'lavender'}],
                       points_for_plot=[{'x': x, 'y': y,'lw':3}], fontsize=20,
                       dpi=150, figure_size=(10, 10),color_ticklabels='white', color_fig='black', color_axes='black',)
        Fig.figure.savefig('data_for_torok/plot')


else:
    print(command)
    print('Unknown command')

# #обязательные параметры:
# 'Th', 'Ph', 'Hum', 'V','dT.ISA',
# #возможные параметры:
# 'Gin', 'n1', 'compr.betta', 'compr.angle', 'comb.Gf', 'turb.betta', 'Gref'
#
# possible_names = {r'^ *(?:T|t)_*(?:h|atm) *$': 'Th',
#                   # ^-начстроки, пробел* - 0 или более пробелов, (:?T|t) - либо T либо t, _* - 0 или более вхождений _, (?:h|atm) - то же самое, пробел* - 0 или более пробелов, $ - конец строки
#                   r'^ *(?:P|p)_*(?:h|atm) *$': 'Ph',
#                   r'^ *(?:dT|dt)_*(?:|ISA|isa) *$': 'dT.ISA',
#                   r'^ *(?:H|h) *$': 'H',
#                   r'^ *(?:M|Mp) *$': 'M',
#                   r'^ *(?:V|Vp) *$': 'V',
#                   r'^ *(?:Hum|fi|Humidity) *$': 'Hum',
#                   r'^ *n_*(?:1|tk|t|t1|tvd|TVD) *$': 'n1',
#                   r'^ *n_*(?:2|t2|tsd|TSD) *$': 'n2',
#                   r'^ *n_*(?:3|t3|tnd|TND) *$': 'n3',
#                   r'^ *n_*(?:st|ST|ts|TS) *$': ('n' + self.named_main_devices['last_turbine_rotor']),
#                   r'^ *n_*(?:pr|priv|corr|corrected)_*(?:1|k|k1|knd|ok) *$': (
#                               self.named_main_devices['first_compressor'].name + '.n_corr'),
#                   r'^ *n_*(?:pr|priv|corr|corrected)_*(?:2|k2|kvd|ck) *$': (
#                               self.named_main_devices['last_compressor'].name + '.n_corr'),
#                   r'^ *N_*(?:|e|v) *$': (self.named_main_devices['last_turbine'].name + '.N'),
#                   r'^ *T_*(?:z|sa)_*(?:tk|t|tvd) *$': (self.named_main_devices['first_turbine'].name + '.throttle.T'),
#                   r'^ *T41 *$': (self.named_main_devices['first_turbine'].name + '.throttle.T'),
#                   r'^ *T_*(?:z|sa)_*(?:t2|tsd) *$': (self.named_main_devices['second_turbine'].name + '.throttle.T'),
#                   r'^ *T_*(?:z|sa)_*(?:t3|tnd|ts|st) *$': (
#                               self.named_main_devices['last_turbine'].name + '.throttle.T'),
#                   r'^ *T_*(?:|in)_*(?:t3|tnd|ts|st) *$': (self.named_main_devices['last_turbine'].name + '.input.T'),
#                   r'^ *T_*out_*(?:t3|tnd|ts|st) *$': (self.named_main_devices['last_turbine'].name + '.output.T'),
#                   r'^ *P_*(?:k1|knd|ok)_*(?:|out) *$': (self.named_main_devices['first_compressor'].name + '.output.P'),
#                   r'^ *P_*(?:k|k2|kvd|ck)_*(?:|out) *$': (
#                               self.named_main_devices['last_compressor'].name + '.output.P'),
#                   r'^ *(?:PR|Pi|PI)_*(?:k|k2|kvd|ck) *$': (self.named_main_devices['last_compressor'].name + '.PRtt'),
#                   r'^ *(?:PR|Pi|PI)_*(?:k1|knd|ok) *$': (self.named_main_devices['first_compressor'].name + '.PRtt'),
#                   r'^ *G_*(?:|in) *$': (self.named_main_devices['ambient'].name + '.outlet.G'),
#                   r'^ *G_*(?:k1|knd|ok)_*(?:pr|rel|corr) *$': (
#                               self.named_main_devices['first_compressor'].name + '.input.G_corr')}
