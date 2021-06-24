# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 16:36:14 2020

@author: Flanker
"""

import Engine as eng
import identification as ident
import pathlib
import logging
import ThermoLog
import sys
ThermoLog.setup_logger('solverLog', 'info.log',logging.DEBUG)
solverLog=logging.getLogger('solverLog')
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

solverLog.info(f'Python interpreter: {sys.executable}')
solverLog.info(f'Python version: {sys.version}')

#1) РАСЧЕТ СТАЦИОНАРНЫХ РЕЖИМОВ
#ВЕРСИЯ ДЛЯ ПК    
Model0=eng.Engine(filename_of_input_data='input_data_GTE170.dat') #исходная непосчитанная модель с заведенными в нее исходными данными
# Model0=eng.Engine() #исходная непосчитанная модель с заведенными в нее исходными данными
#ВЕРСИЯ ДЛЯ ЗАПУСКА ЧЕРЕЗ КОМАНДНУЮ СТРОКУ
# Model0=eng.Engine(Model0.read_modes_from_input_data()) #исходная непосчитанная модель с заведенными в нее исходными данными


# ident_coefs={'ident.compr.G': 0.9144418488510423*1.05, 'ident.compr.Eff': 1.01, 'ident.compr.n': 1.0114248392035308, 'ident.hpt.Cap': 1.0489728162443575, 'ident.hpt.Eff': 1.01, 'ident.hpt.n': 0.9955705812248544, 'ident.pt.Cap': 1.024680027018844, 'ident.pt.Eff': 1.01, 'ident.pt.n': 0.9995930859246324}
# ident_coefs={'ident.compr.G': 0.93, 'ident.compr.n': 1.025}
# Model0.update_ident_coefs(ident_coefs)
# parametric_study_rezults=Model0.parametric_study({'hpt.ident_Cap_value':[0.95,0.975,1,1.02,1.04,1.06,1.08,1.1]}, {'ident.SAS.3':[1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8]})
try:
    rezults=Model0.solve_static_modes()

    Model0.save_rezults_to_file(rezults_data=rezults,filename_where_to_save='results_thermodynamics.csv')
    Model0.make_graphics()
    # Model0.make_graphics_of_maps(rezults)
    solverLog.info(Model0.df)
    solverLog.info('Writing rezults: ok')
except:
    Model0.make_graphics()

# print(f'N={rezults[0].pt.N*1.3596/1000} (2800)')
# print(f'Tztk={rezults[0].hpt.throttle.T} (1448)')
# print(f'Tzts={rezults[0].pt.throttle.T} (1021)')
# print(f'ntk={rezults[0].hpt.n_phys} (0.9771)')
# print(f'Gin={rezults[0].lpc.inlet.G} (8.577)')
# print(f'PR={rezults[0].lpc.PRtt*rezults[0].lpc.PRtt} (15.18)')


# for _rez in rezults:
#     print(_rez.cmbstr.alfa_manual)

#2) ПАРАМЕТРИЧЕСКОЕ ИССЛЕДОВАНИЕ ПО ДВУМ ПАРАМЕТРАМ
# A=ident.identification('input_data_for_identification.dat')
# parametric_study_rezults=Model0.parametric_study({'ident.compr.PR':[0.95,0.975,1,1.025,1.05]}, {'ident.compr.G':[0.9,0.925,0.95,0.975,1.0]})
# main_rez=[]
# for val in parametric_study_rezults:
#     A.compare_experimental_and_calculated_parameters(rezult_list=val['rez'])
#     _x=val['ident.compr.PR']
#     _y=val['ident.compr.G']
#     _z=A.errors['mid_error']
#     _rez=[_x,_y,_z]
#     main_rez.append(_rez)
#     keys=list(val.keys())
# main_rez_df=pd.DataFrame(main_rez,columns=(keys))
# X= main_rez_df[keys[0]].unique()
# Y= np.array(main_rez_df[main_rez_df[keys[0]]==0.95][keys[1]])
# Z=np.array(main_rez_df[keys[2]]).reshape([len(X),len(Y)])

# fig, ax = plt.subplots(constrained_layout=True)
# fig.set_size_inches(10, 10)
# ax.set_xlabel(keys[1],fontsize=15)
# ax.set_ylabel(keys[0],fontsize=15)
# # ax.set_title('Зависимость функции цели от поправочных коэффициентов к пропускной способности ТК и расхода воздуха на охлаждение ТК',fontsize=15)
# p1=ax.contourf(Y,X,Z,cmap='jet')
# p2=plt.contour(Y,X,Z,colors='black',linewidths=0.5)
# ax.clabel(p2, inline=1, fontsize=8,colors='k')
    

#2) УВЯЗКА ПО ЭКСПЕРИМЕНТАЛЬНЫМ ДАННЫМ
# A=ident.identification(filename='input_data_for_identification.dat')#'input_data_for_identification.dat'
# ident_coefs={'ident.compr.G': 0.9199293628659231, 'ident.compr.Eff': 1.01, 'ident.compr.n': 1.0084960343438298, 'ident.hpt.Cap': 1.007383489301189, 'ident.hpt.Eff': 1.01, 'ident.hpt.n': 0.97, 'ident.pt.Cap': 1.0228798633190983, 'ident.pt.Eff': 1.01, 'ident.pt.n': 0.9967182066696666}
# A.model.update_ident_coefs(ident_coefs)
# A.identificate()
# A.make_graphics()

#3) СРАВНЕНИЕ ЭКСПЕРИМЕНТА И РАСЧЕТА
# A=ident.identification('input_data_for_identification.dat')
# ident_coefs= {'ident.compr.G': 0.9144418488510423, 'ident.compr.Eff': 1.01, 'ident.compr.n': 1.0114248392035308, 'ident.hpt.Cap': 1.0489728162443575, 'ident.hpt.Eff': 1.01, 'ident.hpt.n': 0.9955705812248544, 'ident.pt.Cap': 1.024680027018844, 'ident.pt.Eff': 1.01, 'ident.pt.n': 0.9995930859246324}
# A.model.update_ident_coefs(ident_coefs)
# A.rezults_list=A.model.solve_modes()
# A.compare_experimental_and_calculated_parameters()
# print(A.errors['mid_error'])

#4) КОЭФФИЦИЕНТЫ ВЛИЯНИЯ
# A=ident.identification('input_data_for_identification.dat')
# ident_coefs={'ident.compr.G': 0.9288747807134701,'ident.compr.n': 0.99, 'ident.compr.PR': 0.9848647201576244, 'ident.compr.Eff': 1.02, 'ident.cmbstr.sigma': 1.02, 'ident.hpt.Cap': 1.0113917613417625, 'ident.hpt.Eff': 1.03, 'ident.pt.Cap': 1.013833846169274, 'ident.pt.PR': 0.9974841344155987, 'ident.pt.Eff': 1.0201}
# ident_coefs={'ident.compr.G': 0.93}
# A.model.update_ident_coefs(ident_coefs)
# A.calculate_influence()   
# pd.DataFrame(A.influence_dict).to_excel('influence_coefficients.xlsx') #результаты в эксель - там легче обрабатывать
