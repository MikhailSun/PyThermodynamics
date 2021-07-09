import sys
import pandas as pd

import Parser
import devices as dev
import Engine as eng
import thermodynamics as td


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

    if len(params)<3:
        command=params[1]
    else:
        parameters=params[2]
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
