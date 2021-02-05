# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 10:38:01 2018

@author: Sundukov
"""

import numpy as np
from matplotlib import pyplot as plt
from scipy import optimize
import ctypes
import logging
import ThermoLog
import copy
# from scipy.optimize import root 
# from scipy.optimize import minimize

# ThermoLog.setup_logger('solverLog', 'info.log',logging.DEBUG)
solverLog=logging.getLogger('solverLog')
# solverLog.propagate = False

"""
Много данных есть в NASA/TP—2002-211556 и в Third Millennium Ideal Gas and Condensed Phase
Thermochemical Database for Combustion with Updates from Active Thermochemical Tables

Исходные данные по некоторым веществам из NASA Glenn Coefficients for Calculating
Thermodynamic Properties of Individual Species (NASA/TP—2002-211556)

Air Mole%:N2 78.084,O2 20.9476,Ar .9365,CO2 .0319.Gordon,1982.Reac
2 g 9/95 N 1.5617O .41959AR.00937C .00032 .00000 0 28.9651159 -125.530
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8649.264
1.009950160D+04-1.968275610D+02 5.009155110D+00-5.761013730D-03 1.066859930D-05
-7.940297970D-09 2.185231910D-12 -1.767967310D+02-3.921504225D+00
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8649.264
2.415214430D+05-1.257874600D+03 5.144558670D+00-2.138541790D-04 7.065227840D-08
-1.071483490D-11 6.577800150D-16 6.462263190D+03-8.147411905D+00

Ar Ref-Elm. Moore,1971. Gordon,1999.
3 g 3/98 AR 1.00 0.00 0.00 0.00 0.00 0 39.9480000 0.000
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 6197.428
0.000000000D+00 0.000000000D+00 2.500000000D+00 0.000000000D+00 0.000000000D+00
0.000000000D+00 0.000000000D+00 -7.453750000D+02 4.379674910D+00
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 6197.428
2.010538475D+01-5.992661070D-02 2.500069401D+00-3.992141160D-08 1.205272140D-11
-1.819015576D-15 1.078576636D-19 -7.449939610D+02 4.379180110D+00
6000.000 20000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 6197.428
-9.951265080D+08 6.458887260D+05-1.675894697D+02 2.319933363D-02-1.721080911D-06
6.531938460D-11-9.740147729D-16 -5.078300340D+06 1.465298484D+03

CO2 Gurvich,1991 pt1 p27 pt2 p24.
3 g 9/99 C 1.00O 2.00 0.00 0.00 0.00 0 44.0095000 -393510.000
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 9365.469
4.943650540D+04-6.264116010D+02 5.301725240D+00 2.503813816D-03-2.127308728D-07
-7.689988780D-10 2.849677801D-13 -4.528198460D+04-7.048279440D+00
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 9365.469
1.176962419D+05-1.788791477D+03 8.291523190D+00-9.223156780D-05 4.863676880D-09
-1.891053312D-12 6.330036590D-16 -3.908350590D+04-2.652669281D+01
6000.000 20000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 9365.469
-1.544423287D+09 1.016847056D+06-2.561405230D+02 3.369401080D-02-2.181184337D-06
6.991420840D-11-8.842351500D-16 -8.043214510D+06 2.254177493D+03

O2 Ref-Elm. Gurvich,1989 pt1 p94 pt2 p9.
3 tpis89 O 2.00 0.00 0.00 0.00 0.00 0 31.9988000 0.000
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8680.104
-3.425563420D+04 4.847000970D+02 1.119010961D+00 4.293889240D-03-6.836300520D-07
-2.023372700D-09 1.039040018D-12 -3.391454870D+03 1.849699470D+01
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8680.104
-1.037939022D+06 2.344830282D+03 1.819732036D+00 1.267847582D-03-2.188067988D-07
2.053719572D-11-8.193467050D-16 -1.689010929D+04 1.738716506D+01
6000.000 20000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8680.104
4.975294300D+08-2.866106874D+05 6.690352250D+01-6.169959020D-03 3.016396027D-07
-7.421416600D-12 7.278175770D-17 2.293554027D+06-5.530621610D+02

N2 Ref-Elm. Gurvich,1978 pt1 p280 pt2 p207.
3 tpis78 N 2.00 0.00 0.00 0.00 0.00 0 28.0134000 0.000
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8670.104
2.210371497D+04-3.818461820D+02 6.082738360D+00-8.530914410D-03 1.384646189D-05
-9.625793620D-09 2.519705809D-12 7.108460860D+02-1.076003744D+01
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8670.104
5.877124060D+05-2.239249073D+03 6.066949220D+00-6.139685500D-04 1.491806679D-07
-1.923105485D-11 1.061954386D-15 1.283210415D+04-1.586640027D+01
6000.000 20000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 8670.104
8.310139160D+08-6.420733540D+05 2.020264635D+02-3.065092046D-02 2.486903333D-06
-9.705954110D-11 1.437538881D-15 4.938707040D+06-1.672099740D+03

H2O Hf:Cox,1989. Woolley,1987. TRC(10/88) tuv25.
2 g 8/89 H 2.00O 1.00 0.00 0.00 0.00 0 18.0152800 -241826.000
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 9904.092
-3.947960830D+04 5.755731020D+02 9.317826530D-01 7.222712860D-03-7.342557370D-06
4.955043490D-09-1.336933246D-12 -3.303974310D+04 1.724205775D+01
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 9904.092
1.034972096D+06-2.412698562D+03 4.646110780D+00 2.291998307D-03-6.836830480D-07
9.426468930D-11-4.822380530D-15 -1.384286509D+04-7.978148510D+00

CH4 Gurvich,1991 pt1 p44 pt2 p36.
2 g 8/99 C 1.00H 4.00 0.00 0.00 0.00 0 16.0424600 -74600.000
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 10016.202
-1.766850998D+05 2.786181020D+03-1.202577850D+01 3.917619290D-02-3.619054430D-05
2.026853043D-08-4.976705490D-12 -2.331314360D+04 8.904322750D+01
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 10016.202
3.730042760D+06-1.383501485D+04 2.049107091D+01-1.961974759D-03 4.727313040D-07
-3.728814690D-11 1.623737207D-15 7.532066910D+04-1.219124889D+02

CH3 D0(H3C-H): Ruscic,1999. Jacox,1998.
2 g 4/02 C 1.00H 3.00 0.00 0.00 0.00 0 15.0345200 146658.040
200.000 1000.000 7 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 10366.340
-2.876188806D+04 5.093268660D+02 2.002143949D-01 1.363605829D-02-1.433989346D-05
1.013556725D-08-3.027331936D-12 0.000000000D+00 1.408271825D+04 2.022772791D+01
1000.000 6000.000 7 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 10366.340
2.760802663D+06-9.336531170D+03 1.487729606D+01-1.439429774D-03 2.444477951D-07
-2.224555778D-11 8.395065760D-16 0.000000000D+00 7.481809480D+04-7.919682400D+01

Данные по западным топливам:
JP-4 McBride,1996 pp85,93. Hcomb = 18640.BTU/#
0 g 6/96 C 1.00H 1.94 0.00 0.00 0.00 1 13.9661036 -22723.000
298.150 0.0000 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.000
JP-5 Or ASTMA1(L). McBride,1996 pp85,93. Hcomb = 18600.BTU/#
0 g 6/96 C 1.00H 1.92 0.00 0.00 0.00 1 13.9459448 -22183.000
298.150 0.0000 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.000
JP-10(L) Exo-tetrahydrodicyclopentadiene. Smith,1979. React.
0 g 6/01 C 10.00H 16.00 0.00 0.00 0.00 0 136.2340400 -122800.400
298.150 0.0000 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.000
JP-10(g) Exo-tetrahydrodicyclopentadiene.Pri.Com.R.Jaffe 12/00. React.
2 g 6/01 C 10.00H 16.00 0.00 0.00 0.00 0 136.2340400 -86855.900
200.000 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 22997.434
-7.310769440D+05 1.521764245D+04-1.139312644D+02 4.281501620D-01-5.218740440D-04
3.357233400D-07-8.805750980D-11 -8.067482120D+04 6.320148610D+02
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 22997.434
1.220329594D+07-5.794846240D+04 1.092281156D+02-1.082406215D-02 2.034992622D-06
-2.052060369D-10 8.575760210D-15 3.257334050D+05-7.092350760D+02
Jet-A(L) McBride,1996. Faith,1971. Gracia-Salcedo,1988. React.
1 g 2/96 C 12.00H 23.00 0.00 0.00 0.00 1 167.3110200 -303403.000
220.000 550.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 0.000
-4.218262130D+05-5.576600450D+03 1.522120958D+02-8.610197550D-01 3.071662234D-03
-4.702789540D-06 2.743019833D-09 -3.238369150D+04-6.781094910D+02
Jet-A(g) McBride,1996. Faith,1971. Gracia-Salcedo,1988. React.
2 g 8/01 C 12.00H 23.00 0.00 0.00 0.00 0 167.3110200 -249657.000
273.150 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 0.000
-6.068695590D+05 8.328259590D+03-4.312321270D+01 2.572390455D-01-2.629316040D-04
1.644988940D-07-4.645335140D-11 -7.606962760D+04 2.794305937D+02
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 0.000
1.858356102D+07-7.677219890D+04 1.419826133D+02-7.437524530D-03 5.856202550D-07
1.223955647D-11-3.149201922D-15 4.221989520D+05-8.986061040D+02

Данные по продуктам сгорания воздуха и керосина из Gas turbine Performance (стр115):
_Cp=A0+A1*Tz+A2*Tz^2+A3*Tz^3+A4*Tz^4+A5*Tz^5+A6*Tz^6+A7*Tz^7+A8*Tz^8+FAR/(1+FAR)*
*(B0+B1*Tz+B2*Tz^2+B3*Tz^3+B4*Tz^4+B5*Tz^5+B6*Tz^6+B7*Tz^7)
H =A0*TZ + A1/2*TZ^2 + A2/3*TZ^3 + A3/4*TZ^4 + A4/5*TZ^5 + A5/6*TZ^6 + A6/7*TZ^7 +
+ A7/8*TZ^8 + A8/9*TZ^9 + A9 + (FAR/(1+FAR))*(B0*TZ + B1/2*TZ^2 + B2/3*TZ^3 +
+ B3/4*TZ^4 + B4/5*TZ^5 + B5/6*TZ^6 + B6/7*TZ^7 + B8)
Where TZ = TS/1000 
FAR=DeltaH/(LowHeatValue*EfficiencyCombustion)
Entropy: CP/TdT = FT2 - FT1
FT2 = A0*ln(T2Z) + A1*T2Z + A2/2*T2Z^2 + A3/3*T2Z^3 + A4/4*T2Z^4 + A5/5*T2Z^5 +
+ A6/6*T2Z^6 + A7/7*T2Z^7 + A8/8*T2Z^8 + A10 + (FAR/(1 + FAR)) * (B0*ln(T2) +
+ B1*TZ + B2/2*TZ^2 + B3/3*TZ^3 + B4/4*TZ^4 + B5/5*TZ^5 + B6/6*TZ^6 + B7/7*TZ^7 + B9)
FT1 = A0*ln(T1Z) + A1*T1Z + A2/2*T1Z^2 + A3/3*T1Z^3 + A4/4*T1Z^4 + A5/5*T1Z^5 +
+ A6/6*T1Z^6 + A7/7*T1Z^7 + A8/8*T1Z^8 + A10 + (FAR/(1+FAR))*(B0*ln(T1) + B1*TZ +
+ B2/2*TZ^2 + B3/3*TZ^3 + B4/4*TZ^4 + B5/5*TZ^5 + B6/6*TZ^6 + B7/7*TZ^7 + B9)
Where T2Z = TS2/1000, T1Z = TS1/1000 (в формулах FT2 и FT1 что-то напутано  стемпературами, скорее всего в FT2 везде используется T2Z, а в FT1 - T1Z)
A0=0.992313 A1=0.236688 A2=-1.852148 A3=6.083152 A4=-8.893933 A5=7.097112 A6=-3.234725
A7=0.794571 A8=-0.081873 A9=0.422178 A10=0.001053
B0= -0.718874, B1=8.747481, B2= -15.863157, B3=17.254096, B4= -10.233795,
B5=3.081778, B6= -0.361112, B7= -0.003919, B8=0.0555930, B9= -0.0016079.

Kerosene - average composition of C12H23.5 and molecular weight of 167.7 (gas turbine performance - стр588)

характеристики топлива для коммерческой авиации на западе (вероятно ТС-1)
Jet-A(L) McBride,1996. Faith,1971. Gracia-Salcedo,1988. React.
1 g 2/96 C 12.00H 23.00 0.00 0.00 0.00 1 167.3110200 -303403.000
220.000 550.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 0.000
-4.218262130D+05-5.576600450D+03 1.522120958D+02-8.610197550D-01 3.071662234D-03
-4.702789540D-06 2.743019833D-09 -3.238369150D+04-6.781094910D+02
Jet-A(g) McBride,1996. Faith,1971. Gracia-Salcedo,1988. React.
2 g 8/01 C 12.00H 23.00 0.00 0.00 0.00 0 167.3110200 -249657.000
273.150 1000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 0.000
-6.068695590D+05 8.328259590D+03-4.312321270D+01 2.572390455D-01-2.629316040D-04
1.644988940D-07-4.645335140D-11 -7.606962760D+04 2.794305937D+02
1000.000 6000.0007 -2.0 -1.0 0.0 1.0 2.0 3.0 4.0 0.0 0.000
1.858356102D+07-7.677219890D+04 1.419826133D+02-7.437524530D-03 5.856202550D-07
1.223955647D-11-3.149201922D-15 4.221989520D+05-8.986061040D+02
"""

#коэффициенты для расчета свойств воздуха по данным НАСА TP-2002-211556 в диапазоне от 200 до 1000К Mole%:N2 78.084,O2 20.9476,Ar .9365,CO2 .0319.Gordon,1982.Reac 
#coefNASA=np.array([1.009950160E+04,-1.968275610E+02,5.009155110E+00,-5.761013730E-03,1.066859930E-05,-7.940297970E-09,2.185231910E-12,-1.767967310E+02,-3.921504225E+00])

#ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
Tzero=200 #Кельвин, условно нулевая температура относительно которой начинается отсчет абсолютного значения энтропии S в одноименной функции
Pzero=101325 #Паскаль, условно нулевое давление относительно которого начинается отсчет абсолютного значения энтропии S в одноименной функции
Number_of_components=8 #число компонентов в рассматриваемой смеси, это глобальная переменная нужна далее в алгоритмах узлов двигателя для корректного расчета своств рабочего тела. Ставим то число, которое считаем нужным. напрмер для двигателя на керосине это 7: 5 - составляющие воздуха, 1 - жидкий керосин, 1 - газообразный керосин TODO!!! нужно избавиться от этой переменной, нужно чтобы пользователь задавал только состав смеси газа
#состав рабочего тела задаем в формате mass_comp(N2,O2,Ar,CO2,H2O,керосин_газ,керосин_жидкий,метан)
#если в составе будем меняться индекс расположения воды, то нужно откорректировать функцию  WAR_to_moist_air

Runiversal=8.31446261815324 #J/(mol-K) NASA
#MolW_Air=28.9651159 #kg/mol NASA
MolW_N2=28.0134000e-3#kg/mol
MolW_O2=31.9988000e-3#kg/mol 
MolW_CO2=44.00995000e-3#kg/mol
MolW_Ar=39.9480000e-3#kg/mol 
MolW_H2O=18.0152800e-3#kg/mol 
MolW_JetA=167.3110200e-3#kg/mol
MolW_CH4=16.0424600e-3#kg/mol
MolW_CH3=15.0345200e-3#kg/mol
#задаем список со значениями всех молярных масс веществ, используемых в расчете:
MolW_v=np.array((MolW_N2,MolW_O2,MolW_Ar,MolW_CO2,MolW_H2O,MolW_JetA,MolW_JetA,MolW_CH4))

#исходники для расчета свойств веществ: (первый кортеж - коэффициенты для диапазона температур 200-1000К, второй 1000-6000К, третий - теплота образования при температуре 298.15К)
coefsN2=np.array(((2.210371497E+04,-3.818461820E+02, 6.082738360E+00,-8.530914410E-03, 1.384646189E-05,-9.625793620E-09, 2.519705809E-12, 7.108460860E+02,-1.076003744E+01),(5.877124060E+05,-2.239249073E+03, 6.066949220E+00,-6.139685500E-04, 1.491806679E-07,-1.923105485E-11, 1.061954386E-15, 1.283210415E+04,-1.586640027E+01),(0.000)),dtype=object)
coefsO2=np.array(((-3.425563420E+04,4.847000970E+02, 1.119010961E+00, 4.293889240E-03,-6.836300520E-07,-2.023372700E-09, 1.039040018E-12, -3.391454870E+03, 1.849699470E+01),(-1.037939022E+06, 2.344830282E+03, 1.819732036E+00, 1.267847582E-03,-2.188067988E-07,2.053719572E-11,-8.193467050E-16, -1.689010929E+04, 1.738716506E+01),(0.000)),dtype=object)
coefsCO2=np.array(((4.943650540E+04,-6.264116010E+02, 5.301725240E+00, 2.503813816E-03,-2.127308728E-07,-7.689988780E-10, 2.849677801E-13, -4.528198460E+04,-7.048279440E+00),(1.176962419E+05,-1.788791477E+03, 8.291523190E+00,-9.223156780E-05, 4.863676880E-09,-1.891053312E-12, 6.330036590E-16, -3.908350590E+04,-2.652669281E+01),(-393510.000)),dtype=object)
coefsAr=np.array(((0.000000000E+00, 0.000000000E+00, 2.500000000E+00, 0.000000000E+00, 0.000000000E+00,0.000000000E+00, 0.000000000E+00, -7.453750000E+02, 4.379674910E+00),(2.010538475E+01,-5.992661070E-02, 2.500069401E+00,-3.992141160E-08, 1.205272140E-11,-1.819015576E-15, 1.078576636E-19, -7.449939610E+02, 4.379180110E+00),(0.000)),dtype=object)
coefsH2O=np.array(((-3.947960830E+04, 5.755731020E+02, 9.317826530E-01, 7.222712860E-03,-7.342557370E-06,4.955043490E-09,-1.336933246E-12, -3.303974310E+04, 1.724205775E+01),(1.034972096E+06,-2.412698562E+03, 4.646110780E+00, 2.291998307E-03,-6.836830480E-07,9.426468930E-11,-4.822380530E-15, -1.384286509E+04,-7.978148510E+00),(-241826.000)),dtype=object)
coefsJetA=np.array(((-6.068695590E+05, 8.328259590E+03,-4.312321270E+01, 2.572390455E-01,-2.629316040E-04,1.644988940E-07,-4.645335140E-11, -7.606962760E+04, 2.794305937E+02),(1.858356102E+07,-7.677219890E+04, 1.419826133E+02,-7.437524530E-03, 5.856202550E-07,1.223955647E-11,-3.149201922E-15, 4.221989520E+05,-8.986061040E+02),(-249657.000)),dtype=object)#диапазон применимости для газообразного керосина от 273К!!!
coefsJetALiquid=np.array(((-4.218262130E+05,-5.576600450E+03, 1.522120958E+02,-8.610197550E-01, 3.071662234E-03,-4.702789540E-06, 2.743019833E-09, -3.238369150E+04,-6.781094910E+02),(-4.218262130E+05,-5.576600450E+03, 1.522120958E+02,-8.610197550E-01, 3.071662234E-03,-4.702789540E-06, 2.743019833E-09, -3.238369150E+04,-6.781094910E+02),(-303403.0E+01)),dtype=object) #диапазон температуры топлива от 220 до 550К. В данном случае также для жидкого керосина для унификации один и тот же массив коэффициентов повторяется два раза, но тем не менее, жидкий керосин можно считать только в указаном диапазоне от 220 до 550К!!! иначе результаты будут неадекватными
coefsCH4=np.array(((-1.766850998E+05,2.786181020E+03,-1.202577850E+01,3.917619290E-02,-3.619054430E-05,2.026853043E-08,-4.976705490E-12,-2.331314360E+04, 8.904322750E+01),(3.730042760E+06,-1.383501485E+04,2.049107091E+01,-1.961974759E-03,4.727313040E-07,-3.728814690E-11,1.623737207E-15,7.532066910E+04,-1.219124889E+02),(-74600.000)),dtype=object) 
coefsCH3=np.array(((-2.876188806E+04,5.093268660E+02,2.002143949E-01,1.363605829E-02,-1.433989346E-05,1.013556725E-08,-3.027331936E-12, 1.408271825E+04, 2.022772791E+01),(2.760802663E+06,-9.336531170E+03, 1.487729606E+01,-1.439429774E-03, 2.444477951E-07, -2.224555778E-11, 8.395065760E-16, 7.481809480E+04,-7.919682400E+01),(146658.040)),dtype=object)
coefs_v=np.array((coefsN2,coefsO2,coefsAr,coefsCO2,coefsH2O,coefsJetA,coefsJetALiquid,coefsCH4))

R_N2=Runiversal/MolW_N2#J/(kg-K)
R_O2=Runiversal/MolW_O2
R_CO2=Runiversal/MolW_CO2
R_Ar=Runiversal/MolW_Ar
R_H2O=Runiversal/MolW_H2O
R_JetA=Runiversal/MolW_JetA
R_CH4=Runiversal/MolW_CH4
R_CH3=Runiversal/MolW_CH3
R_v=np.array((R_N2,R_O2,R_Ar,R_CO2,R_H2O,R_JetA,R_JetA,R_CH4))

#далее функции для вычисления свойств отдельных веществ
#у функции H и  S ниже "не выставлен" ноль, поэтому использовать их для вычислдения абсолютного значения нельзя! Диапазон применимости функций от 200 до 6000К
#TODO!!! как выяснилось тут: https://stackoverflow.com/questions/52603487/speed-comparison-numpy-vs-python-standard использовать numpy есть смысл только при работе с очень большими массивами, а для обычных операций со скалярами и маленькими массивами стандартные функции питон работают гораздо быстрее! Это надо проверить!
#нужно попробовать задавать массивы с полиномами и с составом через стандартные питоновские функции array.array и сравнить с numpy
#или как вариант вообще пеерписать весь файл thermodynamics.py на Си++, т.к. к функциям из этого файла идут тысячи обращений и как правило производительность упирается в него

def _Cp(T,coefs,R):
    rez=0
    if T<1000:
        v=coefs[0]
    elif T>=1000:
        v=coefs[1]
    for i,c in enumerate(v[:-2]):
        rez+=c*(T**(i-2))
    return rez*R #Дж/моль/К или Дж/кг/К, смотря какую R подставлять в формулу

def _H(T,coefs,R):
    rez=0
    if T<1000:
        v=coefs[0]
    elif T>=1000:
        v=coefs[1]
    rez=-v[0]*(T**(-2))+v[1]*np.log(T)/T+v[2]+v[3]*T/2+v[4]*(T**2)/3+v[5]*(T**3)/4+v[6]*(T**4)/5+v[7]/T
    return rez*R*T #Дж/моль или Дж/кг, смотря какую R подставлять в формулу

def _Sf(T,coefs,R):
    rez=0
    if T<1000:
        v=coefs[0]
    elif T>=1000:
        v=coefs[1]
    rez=-v[0]*(T**(-2))/2-v[1]/T+v[2]*np.log(T)+v[3]*T+v[4]*(T**2)/2+v[5]*(T**3)/3+v[6]*(T**4)/4+v[8]
    return rez*R #Дж/моль/К или Дж/кг/К, смотря какую R подставлять в формулу

#функция для преобразования вектора с мольными долями смеси в массовые доли
def mass_comp(mole_comp):
    EntireMolW=0
    for molP,molW in zip(mole_comp,MolW_v):
        EntireMolW+=molP*molW
    rez=np.array([molP*molW/EntireMolW for molP,molW in zip(mole_comp,MolW_v)])
    return rez
#функция для преобразования вектора с массовыми долями смеси в мольные доли
def mole_comp(mass_comp):
    moleP=np.array([massP/molW for massP,molW in zip(mass_comp,MolW_v)])
    moleEntire=np.sum(moleP)
    return moleP/moleEntire
#молярная масса смеси
def MolW_mix(mole_comp):
    v=[mole_comp_i*MolW_v_i for mole_comp_i,MolW_v_i in zip(mole_comp,MolW_v)]
    rez=np.sum(v)
    return rez
#газовая постоянная смеси
def R_mix(mass_comp):
    return Runiversal/MolW_mix(mole_comp(mass_comp))
#теплоемкость жидкого керосина JetA
#def Cp_JetALiquid(T): #допустимый диапазон от 220 до 550 К
#    rez=0
#    v=coefsJetALiquid[0]
#    for i,c in enumerate(v[:-2]):
#        rez+=c*(T**(i-2))
#    return rez*R_JetA #Дж/кг/К, 
##энтальпия жидкого керосина JetA
#def H_JetALiquid(T): #допустимый диапазон от 220 до 550 К
#    rez=0
#    v=coefsJetALiquid[0]
#    rez=-v[0]*(T**(-2))+v[1]*np.log(T)/T+v[2]+v[3]*T/2+v[4]*(T**2)/3+v[5]*(T**3)/4+v[6]*(T**4)/5+v[7]/T
#    return rez*R_JetA*T #Дж/кг

#вычисление теплоемкости смеси

def Cp(T,mass_comp):
    rez=0
    for mass_comp_i,coefs_i,R_i in zip(mass_comp,coefs_v,R_v):
        rez+=mass_comp_i*_Cp(T,coefs_i,R_i)
    return rez
#вычисление энтальпии смеси

def H(T,mass_comp):
    rez=0
    for mass_comp_i,coefs_i,R_i in zip(mass_comp,coefs_v,R_v):
        rez+=mass_comp_i*_H(T,coefs_i,R_i)
    return rez

#вычисление квази-энтропии смеси
def Sf(T,mass_comp):
    rez=0
    for mass_comp_i,coefs_i,R_i in zip(mass_comp,coefs_v,R_v):
        rez+=mass_comp_i*_Sf(T,coefs_i,R_i)
    return rez
#вычисление настоящей энтропии смеси

def S(P,T,mass_comp,R):
    return Sf(T,mass_comp) - Sf(Tzero,mass_comp) - R*np.log(P / Pzero)
#коэффициент адиабаты

def k(T,mass_comp,R):
    return 1/(1-R/Cp(T,mass_comp))
#вычисление температуры смеси по ее теплоемкости

def T_thru_Cp(Cp_value,mass_comp,x_min,x_max):
    func=lambda T: Cp(T,mass_comp)-Cp_value
    return optimize.brentq(func,x_min,x_max,disp=True)
#вычисление температуры смеси по ее энтальпии

def T_thru_H(H_value,mass_comp,x_min,x_max):
    func=lambda T: H(T,mass_comp)-H_value
    return optimize.brentq(func,x_min,x_max,disp=True)
#вычисление температуры смеси по ее энтропии
def T_thru_S(S_value,mass_comp,x_min,x_max):
    func=lambda T: Sf(T,mass_comp)-S_value
    return optimize.brentq(func,x_min,x_max,disp=True)
#в некоторых задачах необходимо вычислить полные параметры по заданным статическим и без размерной скорости лямбда: TODO!!! это довольно редко используемая но тяжелая функция, тяжелая потому, что здесь в нескольких местах идет обращенеи к функции Critical_Ts - надо упроститиь!
def T_thru_HsTsVcorr(Hs,Ts,V_corr,k_val,mass_comp, R):
    func=lambda Tx: H(Tx,mass_comp)-(Hs+V_corr*V_corr*k(Critical_Ts(Tx,mass_comp,R), mass_comp, R)*R*Critical_Ts(Tx,mass_comp,R)/2)
    _T=Ts/Tau_classic(k_val, V_corr) #эта строка нужна для приближенной оценки верхнего интервала, вннутри котрого нужно искать полную температуру.
    return optimize.root_scalar(func, method='secant', x0=_T,x1=1.00001*_T).root

#вычисление полной энтальпии по известной статической и скорости
def H_thru_HsV(Hs,V):
    return Hs+V*V/2

#поиск конечного давления при известных начальных давлении и температуры и конечной температуре при изоэнтропическом процессе
def P2_thru_P1T1T2(P1,T1,T2,mass_comp,R): #эта штука считает давление независимо от того, сверхкритический или докритический перепад
    return P1*np.exp((Sf(T2,mass_comp) - Sf(T1,mass_comp)) / R)
#поиск конечной температуры при известных начальных давлении и температуры и конечном давлении при изоэнтропическом процессе
def T2_thru_P1T1P2(P1,T1,P2,mass_comp,R,x_min,x_max): #эта штука считает температуру независимо от того, сверхкритический или докритический перепад
    const_value=Sf(T1,mass_comp) + R*np.log(P2 / P1)
    func=lambda T2: Sf(T2,mass_comp) - const_value
    return optimize.brentq(func,x_min,x_max,disp=True)
#поиск критической статической температуры по известным полным параметрам
def Critical_Ts(T,mass_comp,R):
    H_value=H(T,mass_comp)
    func=lambda Ts: (k(Ts,mass_comp,R)*R*Ts) - (2 * (H_value - H(Ts,mass_comp)))
    return optimize.brentq(func,180,T,disp=True)
#статическая температура через энтальпию и число маха
def Ts_thru_HM(H_value,M,mass_comp,R,x_min,x_max):
    func=lambda Ts: H_value-H(Ts,mass_comp)-(M*M*k(Ts,mass_comp,R)*R*Ts/2)
    return  optimize.brentq(func,x_min,x_max,disp=True)
#статическая температура через энтальпию и скорость потока
def Ts_thru_HV(H_value,V,mass_comp,R,x_min,x_max):
    func=lambda Ts: H_value-H(Ts,mass_comp)-((V**2)/2)
    return  optimize.brentq(func,x_min,x_max,disp=True)
#статическая температура через расход, полные давление и температуру и площадь. Если перепад сверхкритический, то считает из условия запирания

def Ts_thru_GPTHF(G,P,T,Hval,F,Ts_cr,mass_comp,R): #медленная функция, если есть возможность, лучше ее не использовать
    func=lambda Ts: G**2-(P2_thru_P1T1T2(P,T,Ts,mass_comp,R)/R/Ts*F)**2*(2*(Hval-H(Ts,mass_comp)))
    Ts= optimize.brentq(func,Ts_cr,T,disp=True)
    return Ts

#давление насыщенных паров (Buck equation из википедии)
def P_sat_vapour1(T):
    T=T-273.15
    if T>=0:
        return 0.61121*np.exp((18.678-T/234.5)*(T/(257.14+T)))*1000
    else:
        return 0.61115*np.exp((23.036-T/333.7)*(T/(279.82+T)))*1000
#давление насыщенных паров (из Gas Turbine Performance)
def P_sat_vapour2(P,T):
    return((1.0007+(3.46e-5)*(P/1000))*0.61121*np.exp(17.502*(T-273.15)/(T-32.25))*1000)
#формула для расчета удельной влажности/влагосодержания/отношения массы пара к массе сухогов воздуха
def WAR(rel_hum, P, T, mass_comp_dry_air ): #за основуную формулу для поиска давления насыщенных паров примем пока что P_sat_vapour1, т.е. без учета давления
    if rel_hum==0:   #!!!важно знать, что эта формула работает правильно при температуре возуха менее 100 Цельсий!!! Потребностей в бОльших температурах не должно возникать! Иначе результат функциий может быть отрицательным, т.е. не физичным
        rez=0
    else:
        
        Pvap = P_sat_vapour1(T)*rel_hum
        if (P-Pvap)<0:
            text="В функции для вычисления влагосодержания температура при которой вычисляестя давление пара неадекватно большое. Tатм={T}, Pатм={P}, Pvapor={Pvap}, Hum={rel_hum}  Возможна ошибка."
            raise ValueError(text)
        Ro_vap=Pvap/T/R_H2O
        Ro_dry_air=(P-Pvap)/T/R_mix(mass_comp_dry_air)
        rez=((Ro_vap)/(Ro_dry_air)) #отношение плотностей пара и сухого! воздуха
    return rez

#расчет относительной влажности по влагосодержанию        
def Rel_humidity(WAR,P,T):
    Psat_vap = P_sat_vapour1(T) #давление насыщенного пара
    Pvap=P*WAR/(1+WAR)
    return Pvap/Psat_vap


def WAR_to_moist_air(WAR,mass_comp_dry_air):
    mass_comp_water=np.empty(Number_of_components) #!!!размер массива должен соответствовать числу составляющих газ
    mass_comp_water[:]=0
    mass_comp_water[4]=1 #!здесь важно чтобы индекс соответствоваол порядковому номеру воды в массиве mass_comp
    rez=mass_comp_dry_air*(1-WAR)+mass_comp_water*WAR
    return rez

def T_ISA(H):
    if H<11000:
        T=288.15-0.0065*H
    elif H<24994 and H>=11000:
        T=216.65
    elif H<30000 and H>=24994:
        T=216.65+0.0029892*(H-24994)
    return T

def P_ISA(H):
    if H<11000:
        P=101325*(288.15/T_ISA(H))**(-5.25588)
    elif H<24994 and H>=11000:
        P=22.63253/np.exp(0.000157689*(H-10998.1))
    elif H<30000 and H>=24994:
        P=2.5237*(216.65/T_ISA(H))**11.8
    return P

def Dyn_visc_klimov(T):
    _T=T/1000 #динамический коэффициент вязкости, определяемый для расчета поправок к характеристикам турбины по данным "Математическая модель двигателя 26.616.0004-2016ММ1", стр27
    return ((_T**1.274511)*np.exp(1.455223-0.3054685*_T))+1 #для расчета других двигателей лучше стоит убедиться в достоверности этой формулы или использовать данные из NASA


#TODO!!! сделать отдельный пул формул из классической газодинамики, подумать какие формулы нужны, в частности обязательно газо-динамические функции

def Ps_Pt(V_corr,k): #газодинамическая функция по классической формуле: отношение статического к полному давлению в зависимости от приведенной скорости
    a=k-1
    b=k+1
    rez=(1-a*V_corr**2/b)**(k/a)
    return rez

#функция для вычисления состава продуктов сгорания топлива по известному относительному расходу топлива
def RelativeFuelFlow2GasMixture(dry_air,stoichiometric_gas,rel_fuel_flow,L):
    Gfuel=rel_fuel_flow #отн расход топлива = расход топлива/расход воздуха
    Gair_burnt=Gfuel*L
    Gair_unburnt=1-Gair_burnt
    gas_mixture=(Gair_burnt+Gfuel)/(1+Gfuel)*stoichiometric_gas+Gair_unburnt/(1+Gfuel)*dry_air
    return gas_mixture

#классические газодинамические функции, которые в общем-то не совсем точны
def Pi_classic(k,V_corr): #отношение статического давления к полному
    return (1-V_corr*V_corr*((k-1)/(k+1)))**(k/(k-1))

def Tau_classic(k,V_corr): #отношенеи статической температуры  к полной
    return (1-V_corr*V_corr*((k-1)/(k+1)))


#TODO!!! ГЛОБАЛЬНО! нужно переписать классы IsentropicFlow и CrossSection так, чтобы они стали универсальными, чтобы максимально автоматизировано, чтобы пользователь сильно не парился по поводу того, какие параметры заданы, какие нет, чтобы классы сами контролировали переопределенные исходные данные и отсюда выдавали решение или предупреждение
# подумать, стоит ли переписать эти классы через свойства @property через сеттеры, через введение параметров, котрые бы отслеживали заданные и рассчитываемые параметры, чтобы при итерационном расчете можно было сбрасывать значения рассчитываемых параметров. Использование @property исключает необходимоть рассчитывать ненужные параметры, что полезно для быстродействия

#класс для описания всех параметров изоэнтропического процесса без привязки к геометрии, т.е. условие сверхкритического/докритического потока здесь не производится
class IsentropicFlow():
    #!!!НУЖНО ПОРАБОТАТЬ НАД ОПТИМИЗАЦИЕЙ ЭТОГО КЛАССА, ТК ОН ОДИН ИЗ БАЗОВЫХ И К НЕМУ ИДЕТ СОТНИ И ТЫСЯЧИ ОБРАЩЕНИЙ
    def __init__(self,name_of_parent=''):
        #СНАЧАЛА ПЕРЕЧИСОЯЕМ ВСЕ ПАРАМЕТРЫ ИСПОЛЬЗУЕМЫЕ ДЛЯ ОПИСАНИЕ СОСТОЯНИЯ В СЕЧЕНИИ ПОТОКА
        #TODO!! попробовать использовать вместо скалярных значений массив ndarray c одним значением, это нужно для того, чтобы была возможность передавать значения по ссылке. По тестам если использовать массив с одним числом вместо скаляра на быстродействии это скажется только по части записи, чтение по скорости не отдичается. Зато передача параметра по ссылке может придать ускорение в други
        self.was_edited = False #флаг для отслеживания того, была ли структура отредактирована в процессе выполнения метода
        self.name_of_parent = name_of_parent
        # 1 группа параметров зависящих только от состава смеси
        self.mass_comp=np.empty(Number_of_components) #!!!размер массива должен соответствовать числу составляющих газ
        self.mass_comp[:]=np.nan
        self.R=np.nan
        # 2 группа полные параметры смеси газа
        self.P=np.nan 
        self.T=np.nan
        self.Ro=np.nan
        self.Cp=np.nan
        self.Cv=np.nan
        self.k=np.nan
        self.H=np.nan
        self.Sf=np.nan
        self.S = np.nan
        # 3 группа статические параметры смеси газа
        self.Ps=np.nan
        self.Ts=np.nan
        self.Ros=np.nan
        self.Cps = np.nan
        self.Cvs = np.nan
        self.ks = np.nan
        self.Hs=np.nan
        self.Sfs=np.nan
        self.Ss= np.nan
        self.Vsnd=np.nan
        self.flowdensity=np.nan 
        # 4 газодинамические параметры смеси газа
        self.pi = np.nan 
        self.tau = np.nan
        self.q = np.nan
        # 5 группа критические параметры
        self.Ts_cr=np.nan
        self.Ps_cr=np.nan
        self.Ros_cr=np.nan
        self.V_cr=np.nan
        self.k_cr=np.nan
        self.flowdensity_cr=np.nan
    
    #ОПРЕДЕЛИМ МЕТОДЫ КЛАССА IsentropicProcess
    def calculate_R(self):
        if np.isnan(self.R) and not(np.all(np.isnan(self.mass_comp))):
            self.R = R_mix(self.mass_comp)
            self.was_edited = True
    def calculate_P(self):
        if np.isnan(self.P):
            TRo=not(np.isnan(self.R)) and not(np.isnan(self.T)) and not(np.isnan(self.Ro))
            TTsPs=not(np.isnan(self.T)) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)) and not(np.all(np.isnan(self.mass_comp)))
            if int(TRo) + int(TTsPs)>1:
                solverLog.warning('WARNING! calculate_P: Overdetermined source data')
            if TRo:
                self.P = self.R*self.T*self.Ro
                self.was_edited = True
            if TTsPs:
                if self.Ts>=self.T:
                    solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_P: Ts({Ts})>T({T})'.format(T=self.T,Ts=self.Ts))
                self.P=P2_thru_P1T1T2(self.Ps,self.Ts,self.T,self.mass_comp,self.R)
                self.was_edited = True
    def calculate_T(self):
        if np.isnan(self.T):
            PRo=not(np.isnan(self.R)) and not(np.isnan(self.P)) and not(np.isnan(self.Ro))
            H=not(np.isnan(self.H)) and not(np.all(np.isnan(self.mass_comp)))
            PTsPs=not(np.isnan(self.P)) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)) and not(np.all(np.isnan(self.mass_comp)))
            if int(PRo) + int(H) + int(PTsPs)>1:
                solverLog.warning('WARNING! calculate_T: Overdetermined source data')
            if PRo: #ищем температуру из P/Ro=R*T
                self.T = self.P / self.Ro / self.R
                self.was_edited = True
            if H:
                self.T=T_thru_H(self.H,self.mass_comp,150,3000)
                self.was_edited = True
            if PTsPs:
                if self.Ps>=self.P:
                    solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_T: Ps({Ps})>P({P})'.format(P=self.P,Ps=self.Ps))
                self.T=T2_thru_P1T1P2(self.Ps,self.Ts,self.P,self.mass_comp,self.R,150,3000)
                self.was_edited = True
    def calculate_Ro(self):
        if np.isnan(self.Ro) and not(np.isnan(self.R)) and not(np.isnan(self.P)) and not(np.isnan(self.T)): #ищем плотность из P/Ro=R*T
            self.Ro = self.P / self.R / self.T
            self.was_edited = True
    def calculate_Cp(self):
        if np.isnan(self.Cp) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))):
            self.Cp = Cp(self.T, self.mass_comp)
            self.was_edited = True
    def calculate_Cv(self):
        if np.isnan(self.Cv) and not(np.isnan(self.k)) and not(np.isnan(self.Cp)):
            self.Cv = self.Cp / self.k
            self.was_edited = True
    def calculate_k(self):
        if np.isnan(self.k) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.k = k(self.T, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_H(self):
        if np.isnan(self.H) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))):
            self.H = H(self.T, self.mass_comp)
            self.was_edited = True
    def calculate_Sf(self):
        if np.isnan(self.Sf) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))):
            self.Sf = Sf(self.T, self.mass_comp)
            self.was_edited = True
    def calculate_S(self):
        if np.isnan(self.S) and not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.S = S(self.P,self.T,self.mass_comp,self.R)
            self.was_edited = True
            
    def calculate_Ps(self):
        if np.isnan(self.Ps):
            if not(np.isnan(self.R)) and not(np.isnan(self.Ts)):
                TsPT=not(np.isnan(self.P)) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp)))
                TsRos=not(np.isnan(self.Ros))
                if int(TsPT) + int(TsRos)>1:
                    solverLog.warning('WARNING! calculate_Ps: Overdetermined source data')
                if TsPT: #ищем давление через энтропию, дельта энтропии = 0
                    if self.Ts>=self.T:
                        solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_Ps: Ts({Ts})>T({T})'.format(T=self.T,Ts=self.Ts)) 
                    self.Ps = P2_thru_P1T1T2(self.P, self.T, self.Ts, self.mass_comp,self.R)
                    self.was_edited = True
                elif TsRos: #ищем давление из P/Ro=R*T
                    self.Ps = self.R*self.Ts*self.Ros
                    self.was_edited = True
    def calculate_Ts(self):
        if np.isnan(self.Ts): #ищем температуру из P/Ro=R*T или из H=Hстатика+V^2/2
            RosPs=not(np.isnan(self.Ros)) and not(np.isnan(self.Ps)) and not(np.isnan(self.R))
            TPPs=not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.Ps)) and not(np.isnan(self.R))
            Hs=not(np.isnan(self.Hs)) and not(np.all(np.isnan(self.mass_comp)))
            if int(RosPs) + int(TPPs) + int(Hs)>1:
                solverLog.warning('WARNING! calculate_Ts: Overdetermined source data')
            if RosPs:
                self.Ts = self.Ps / self.Ros / self.R
                self.was_edited = True
            elif TPPs:
                if self.Ps>=self.P:
                    solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_Ts: Ps({Ps})>P({P})'.format(P=self.P,Ps=self.Ps))         
                self.Ts=T2_thru_P1T1P2(self.P,self.T,self.Ps,self.mass_comp,self.R,150,self.T)
                self.was_edited = True
            elif Hs:
                self.Ts = T_thru_H(self.Hs, self.mass_comp,150,self.T)
                self.was_edited = True      
    def calculate_Ros(self):
    	if np.isnan(self.Ros) and not(np.isnan(self.R)) and not(np.isnan(self.Ps)) and not(np.isnan(self.Ts)): #ищем плотность из P/Ro=R*T или G=Ro*V*F
            self.Ros = self.Ps / self.R / self.Ts
            self.was_edited = True
    def calculate_Cps(self):
        if np.isnan(self.Cps) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))):
            self.Cps = Cp(self.Ts, self.mass_comp)
            self.was_edited = True
    def calculate_Cvs(self):
        if np.isnan(self.Cvs) and not(np.isnan(self.Cps)) and not(np.isnan(self.ks)):
            self.Cvs = self.Cps / self.ks
            self.was_edited = True
    def calculate_ks(self):
        if np.isnan(self.ks) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.ks = k(self.Ts, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_Hs(self):
        if np.isnan(self.Hs) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))):
            self.Hs = H(self.Ts, self.mass_comp)
            self.was_edited = True
    def calculate_Sfs(self):
        if np.isnan(self.Sfs) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))):
            self.Sfs = Sf(self.Ts, self.mass_comp)
            self.was_edited = True
    def calculate_Ss(self):
        if np.isnan(self.Ss) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.Ss = S(self.Ps, self.Ts, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_Vsnd(self):
        if not_exist(self.Vsnd) and exist(self.Ts) and exist(self.R) and exist(self.ks):
            self.Vsnd=np.sqrt(self.ks*self.R*self.Ts)
            self.was_edited=True
    def calculate_flowdensity(self): 
        if np.isnan(self.flowdensity) and not(np.isnan(self.Ros)) and not(np.isnan(self.H)) and not(np.isnan(self.Hs)):
            if self.Hs>self.H:
                solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_flowdensity: Hs({Hs})>H({H})'.format(H=self.H,Hs=self.Hs))       
            self.flowdensity=self.Ros*np.sqrt(2*(self.H-self.Hs))
            self.was_edited = True 
    
    def calculate_pi(self):
        if np.isnan(self.pi) and not(np.isnan(self.P)) and not(np.isnan(self.Ps)):
            self.pi = self.Ps / self.P
            self.was_edited = True
    def calculate_tau(self): 
        if np.isnan(self.tau) and not(np.isnan(self.T)) and not(np.isnan(self.Ts)):
            self.tau = self.Ts / self.T
            self.was_edited = True
    def calculate_q(self):#относительная плотность потока  (газодинамическая функция)
        if np.isnan(self.q) and not(np.isnan(self.flowdensity)) and not(np.isnan(self.flowdensity_cr)):
            self.q = self.flowdensity/ self.flowdensity_cr
            self.was_edited = True

    def calculate_Ts_cr(self):
        if np.isnan(self.Ts_cr) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.Ts_cr=Critical_Ts(self.T,self.mass_comp,self.R)
            self.was_edited = True
    def calculate_Ps_cr(self):
        if np.isnan(self.Ps_cr) and not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.isnan(self.Ts_cr)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            if self.Ts>self.T:
                solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_Ps_cr: Ts({Ts})>T({T})'.format(T=self.T,Ts=self.Ts))  
            self.Ps_cr=P2_thru_P1T1T2(self.P,self.T,self.Ts_cr,self.mass_comp,self.R)
            self.was_edited = True
    def calculate_Ros_cr(self):
        if np.isnan(self.Ros_cr) and not(np.isnan(self.Ps_cr)) and not(np.isnan(self.Ts_cr)) and not(np.isnan(self.R)):
            self.Ros_cr=self.Ps_cr/self.Ts_cr/self.R
            self.was_edited = True
    def calculate_k_cr(self):
        if np.isnan(self.k_cr) and not(np.isnan(self.Ts_cr)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.k_cr = k(self.Ts_cr, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_V_cr(self):
        if np.isnan(self.V_cr) and not(np.isnan(self.Ts_cr)) and not(np.isnan(self.R)) and not(np.isnan(self.k_cr)):
            self.V_cr=np.sqrt(self.k_cr*self.R*self.Ts_cr)
            self.was_edited = True
    def calculate_flowdensity_cr(self):
        if np.isnan(self.flowdensity_cr) and not(np.isnan(self.V_cr)) and not(np.isnan(self.Ps_cr)):
            self.flowdensity_cr = self.V_cr*self.Ros_cr
            self.was_edited = True
            
    def calculate(self): #расчет всех параметров при наличии возможности
        self.was_edited = False
        self.calculate_R()
        self.calculate_T()
        self.calculate_P()
        self.calculate_Ro()
        self.calculate_Cp()
        self.calculate_k()
        self.calculate_Cv()
        self.calculate_H()
        self.calculate_Sf()
        self.calculate_S()

        self.calculate_Ts()
        self.calculate_Ps()
        self.calculate_Ros()
        self.calculate_Cps()
        self.calculate_ks()
        self.calculate_Cvs()
        self.calculate_Hs()
        self.calculate_Sfs()
        self.calculate_Ss()
        self.calculate_Vsnd()
        self.calculate_flowdensity()
        
        self.calculate_pi()
        self.calculate_tau()
        self.calculate_q()

        self.calculate_Ts_cr()
        self.calculate_Ps_cr()
        self.calculate_Ros_cr()
        self.calculate_k_cr()
        self.calculate_V_cr()
        self.calculate_V_cr()
        self.calculate_flowdensity_cr()

        if (self.was_edited):
            self.calculate()
            
    def copy_statPar_to_totPar(self):
        self.Cp=self.Cps
        self.Cv=self.Cvs
        self.H=self.Hs
        self.P=self.Ps
        self.Ro=self.Ros
        self.S=self.Ss
        self.Sf=self.Sfs
        self.T=self.Ts
        self.k=self.ks
        self.pi=1.0
        self.tau=1.0
            
    def status(self):
        for att in dir(self):
            if att[0]!='_' and att[0:9]!='calculate' and att[0:6]!='status' and att[0:10]!='was_edited' and att[0:4]!='copy':
                print (att,' = ', getattr(self,att)) 

#класс для описания всех параметров в сечении потока
class CrossSection():
    #смысл этого класса в том, что он разрешает процессы, происходящие в неком абстрактном сечении потока. Здесь задаются параметры: полные параметры потока, статические, статическое "заднее" давление, которое равно обычному статическому при дозвуковом перепаде и не равно ему при сверхзвуковом, расход смеси газов, площадь сечения, скорость в сечении
    
    #!!!НУЖНО ПОРАБОТАТЬ НАД ОПТИМИЗАЦИЕЙ ЭТОГО КЛАССА, ТК ОН ОДИН ИЗ БАЗОВЫХ И К НЕМУ ИДЕТ СОТНИ И ТЫСЯЧИ ОБРАЩЕНИЙ
    #!!!Для задачи гидравлики используем допущение, что давление в полости на входе в сечение интерпретируется как полное, а давление в полости на выходе - как статическое - стр154 Султанян, самый низ страницы TODO! хотя на мой взгляд это неочевидно, нужно подумать над адекватностью такого допущения
    #!!!продолжение: вомзожно это допущение имеет место быть тогда, когда узел - это абстракция, которая не имеет конкретной геометрии, а значит и невозможно вычислить статическое давление. В литературе это называется plenum. Как называется полость с известной геометрией, где есть динамическая составляющая и статические параметры? chamber/vortex?
    def __init__(self,name_of_parent=''):
        #СНАЧАЛА ПЕРЕЧИСОЯЕМ ВСЕ ПАРАМЕТРЫ ИСПОЛЬЗУЕМЫЕ ДЛЯ ОПИСАНИЕ СОСТОЯНИЯ В СЕЧЕНИИ ПОТОКА
        #TODO!! попробовать использовать вместо скалярных значений массив ndarray c одним значением, это нужно для того, чтобы была возможность передавать значения по ссылке. По тестам если использовать массив с одним числом вместо скаляра на быстродействии это скажется только по части записи, чтение по скорости не отдичается. Зато передача параметра по ссылке может придать ускорение в други
        
        self.was_edited = True #флаг для отслеживания того, была ли структура отредактирована в процессе выполнения метода
        self.name_of_parent = name_of_parent #имя родительского узла, необходимо, чтобы при возникновении ошибки выводить в лог это имя
        # 1 группа параметров зависящих только от состава смеси
        self.mass_comp=np.empty(Number_of_components) #!!!размер массива должен соответствовать числу составляющих газ
        self.mass_comp[:]=np.nan
        self.R=np.nan
        # 2 группа полные параметры смеси газа в сечении
        self.P=np.nan 
        self.T=np.nan
        self.Ro=np.nan
        self.Cp=np.nan
        self.Cv=np.nan
        self.k=np.nan
        self.H=np.nan
        self.Sf=np.nan
        self.S = np.nan
        # 3 группа статические параметры смеси газа в сечении. Важно понимать, что обычно когда задается статическое давление на вызоде сечения, оно не обязательно равно статическому! 
        self.Ps_back=np.nan#фактически имеющееся статическое давление на выходе из сечения, т.е. оно не привязано к параметрам перед сечением
        self.Ps=np.nan
        self.Ts=np.nan
        self.Ros=np.nan
        self.Cps = np.nan
        self.Cvs = np.nan
        self.ks = np.nan
        self.Hs=np.nan
        self.Sfs=np.nan
        self.Ss= np.nan
        self.Vsnd=np.nan
        self.flowdensity_thru_Ps=np.nan 
        # 4 газодинамические параметры смеси газа
        self.pi = np.nan 
        self.tau = np.nan
        self.q = np.nan
        # 5 группа критические параметры
        self.Ts_cr=np.nan
        self.Ps_cr=np.nan
        self.Ros_cr=np.nan
        self.V_cr=np.nan
        self.k_cr=np.nan
        self.flowdensity_cr=np.nan
        # 6 расходные/скоростные параметры, площадь сечения
        self.G=np.nan
        self.G_corr=np.nan #приведенный расход
        self.G_corr_s = np.nan #приведенный расход по статическим параметрам
        self.capacity=np.nan #пропускная способность вычисляемая на основе полных параметров, здесь не учитывается эффект запирания потока, если он есть, просто G*T**0.5/P
        self.capacity_s=np.nan #пропускная способность по статическим параметрам, возможное запирание не учитывается
        # self.flowdensity_thru_Ps_back=np.nan #плотность тока - отношение расхода к площади поперечного сечения
        self.flowdensity_thru_G=np.nan
        self.F=np.nan #площадь сечения
        self.V_corr=np.nan #безразмертная скорость лямбда
        self.M=np.nan #число Маха
        self.V=np.nan #скорость
        # 7 группа
        #    Dhydraulic = np.nan //гидравлический диаметр, необходим прежде всего для вычисления числа Рейнольдса
        #    Re=np.nan //Рейнольдс
        #    dynamic_viscosity = np.nan //динамическая вязкость
        #    kinematic_viscosity = np.nan //кинематическая вязкость
        # 8 группа
        self.Tref = 288.15 #температура для расчета приведенных параметров
        self.Pref = 101325.0 #давление для расчета приведенных параметров
        # 9 параметры импульса и силы от давления в сечении
        self.Force=np.nan
        self.Impulse=np.nan
        
        self.flowdensity_error=np.nan
        # self.aux=IsentropicFlow(self.name_of_parent) #TODO! помоему эту штуку aux не нужно хранить в привязке к объекту, она создается и используется только при конкретных вызовах разных calculation. надо подумать и возможно убрать ее, исправив все calculation

        
    #ОПРЕДЕЛИМ МЕТОДЫ КЛАССА CrossSection
    def is_total_parameters_exist(self):
        return (exist(self.P) or exist(self.Ro)) and (exist(self.T) or exist(self.H))
    
    def is_static_parameters_exist(self):
        return (exist(self.Ps) or exist(self.Ros)) and (exist(self.Ts) or exist(self.Hs))
    
    def is_velocity_exist(self):
        return (exist(self.V) or exist(self.M) or exist(self.V_corr))
            
    def calculate_G(self):
        if np.isnan(self.G):
            a1=not(np.isnan(self.Ros)) and not(np.isnan(self.V)) and not(np.isnan(self.F))
            a2=not(np.isnan(self.G_corr)) and not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.isnan(self.Tref)) and not(np.isnan(self.Pref))
            a3=not(np.isnan(self.capacity)) and not(np.isnan(self.T)) and not(np.isnan(self.P)) 
            if int(a1) + int(a2)+ int(a3)>1:
                solverLog.warning('WARNING! calculate_G: Overdetermined source data')
            if a2:
                self.G=self.G_corr/(np.sqrt(self.T/self.Tref)*self.Pref/self.P)
                self.was_edited = True
            elif a3:
                self.G=self.capacity/(np.sqrt(self.T))*self.P
                self.was_edited = True
            elif a1:
                self.G = self.Ros*self.V*self.F
                self.was_edited = True
    def calculate_G_corr(self):
        if np.isnan(self.G_corr) and not(np.isnan(self.capacity)) and not(np.isnan(self.Pref)) and not(np.isnan(self.Tref)):
            self.G_corr = self.capacity*self.Pref / np.sqrt(self.Tref)
            self.was_edited = True
    def calculate_G_corr_s(self):
        if np.isnan(self.G_corr_s) and not(np.isnan(self.capacity_s)) and not(np.isnan(self.Pref)) and not(np.isnan(self.Tref)):
            self.G_corr_s = self.capacity_s*self.Pref / np.sqrt(self.Tref)
            self.was_edited = True
    def calculate_capacity(self):
        if np.isnan(self.capacity) and not(np.isnan(self.G)) and not(np.isnan(self.T)) and not(np.isnan(self.P)):
            self.capacity = self.G*np.sqrt(self.T) / self.P
            self.was_edited = True
    def calculate_capacity_s(self):
        if np.isnan(self.capacity_s) and not(np.isnan(self.G)) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)):
            self.capacity_s = self.G*np.sqrt(self.Ts) / self.Ps
            self.was_edited = True
    def calculate_flowdensity_thru_G(self):
        if np.isnan(self.flowdensity_thru_G):
            if not(np.isnan(self.G)) and not(np.isnan(self.F)):
                self.flowdensity_thru_G=self.G/self.F
                self.was_edited = True
    def calculate_F(self):
        if np.isnan(self.F) and not(np.isnan(self.G)) and not(np.isnan(self.Ros)) and not(np.isnan(self.V)):
            self.F = self.G / self.Ros / self.V
            self.was_edited = True
    def calculate_V(self):
        if (np.isnan(self.V)):
            #TODO! бывают ситуации, когда параметр можно вычислить разными способами, т.е. есть различные наборы данных, позволяющих вычислить этот параметр, нужно как-то это учесть. Как - пока не придумал:(
            GRosF=not(np.isnan(self.G)) and not(np.isnan(self.Ros)) and not(np.isnan(self.F)) #and np.isnan(self.Ps) and np.isnan(self.Ts) 
            VcrVcorr=not(np.isnan(self.V_cr)) and not(np.isnan(self.V_corr)) #and not(np.isnan(self.R)) and not(np.all(np.isnan(self.mass_comp)))
            MVsnd=not(np.isnan(self.M)) and not(np.isnan(self.Vsnd))
            # HHs=not(np.isnan(self.H)) and not(np.isnan(self.Hs))
            if int(GRosF) + int(VcrVcorr)+int(MVsnd)>1:
                solverLog.warning('WARNING! calculate_V: Overdetermined source data')
            if VcrVcorr:
                self.V = self.V_cr*self.V_corr
                self.was_edited = True
            elif MVsnd:
                # Vsnd=np.sqrt(self.ks*self.R*self.Ts)
                self.Vsnd
                self.V = self.M*self.Vsnd
                self.was_edited = True
            # elif HHs:
            #     self.V=np.sqrt(2*(self.H-self.Hs))
            #     self.was_edited = True
            elif GRosF:
                self.V = self.G / self.Ros / self.F
                self.was_edited = True
    def calculate_V_corr(self):
        if np.isnan(self.V_corr) and not(np.isnan(self.V)) and not(np.isnan(self.V_cr)):
            self.V_corr=self.V/self.V_cr
            self.was_edited = True
    def calculate_M(self):
        if np.isnan(self.M) and not(np.isnan(self.V)) and not(np.isnan(self.Vsnd)):
            self.M = self.V / self.Vsnd
            self.was_edited = True
    def calculate_Force(self):
        if np.isnan(self.Force) and not(np.isnan(self.Ps)) and not(np.isnan(self.F)):
            self.Force=self.Ps*self.F
            self.was_edited = True
    def calculate_Impulse(self):
        if np.isnan(self.Impulse) and not(np.isnan(self.G)) and not(np.isnan(self.V)):
            self.Impulse=self.G*self.V
            self.was_edited = True
    
    def calculate_thru_FGPback(self): #расчет с учетом возможного критического перепада, рассчитывается невязка по плотности тока. Расчет можно считать корректным когда плотиность тока посчитанная через расход и  через подпорное давление Pback равны, иначе расчет корректным считать нельзя! Используется для расчета сопла, когда заранее неизвестно какой пеерпад на сопле - докритика или сверхкритика
        if self.is_total_parameters_exist() and exist(self.F) and exist(self.G) and exist(self.Ps_back)and not(np.isnan(all(self.mass_comp))):
            #TODO! попробовать сделать так, чтобы алгоритм сам смотрел какие параметры заданы в сrosssection и передавал их внутрь aux без ручного присваивания как сейчас
            aux=IsentropicFlow(self.name_of_parent)
            aux.mass_comp=self.mass_comp
            aux.R=self.R
            aux.P=self.P
            aux.T=self.T
            aux.Ro=self.Ro
            aux.Cp=self.Cp
            aux.Cv=self.Cv
            aux.k=self.k
            aux.H=self.H
            aux.Sf=self.Sf
            aux.S=self.S
            # aux.Ps=self.Ps_back
            aux.calculate()
            self.flowdensity_thru_G=self.G/self.F
            
            if aux.flowdensity_cr<self.flowdensity_thru_G:
                self.flowdensity_error=(self.flowdensity_thru_G-aux.flowdensity_cr)/self.flowdensity_thru_G
            else:
                if self.Ps_back<aux.Ps_cr:
                    aux.Ps=aux.Ps_cr
                else:
                    aux.Ps=self.Ps_back
                aux.calculate()
                self.flowdensity_error=(self.flowdensity_thru_G-aux.flowdensity)/self.flowdensity_thru_G
            self.R=aux.R
            self.P=aux.P
            self.T=aux.T
            self.Ro=aux.Ro
            self.Cp=aux.Cp
            self.Cv=aux.Cv
            self.k=aux.k
            self.H=aux.H
            self.Sf=aux.Sf
            self.S = aux.S
            self.Ps=aux.Ps
            self.Ts=aux.Ts
            self.Ros=aux.Ros
            self.Cps = aux.Cps
            self.Cvs = aux.Cvs
            self.ks = aux.ks
            self.Hs=aux.Hs
            self.Sfs=aux.Sfs
            self.Ss= aux.Ss
            self.Vsnd=aux.Vsnd
            self.flowdensity_thru_Ps=aux.flowdensity
            # self.flowdensity_thru_Ps_back=aux.flowdensity
            self.pi = aux.pi
            self.tau = aux.tau
            self.q = aux.q
            self.Ts_cr=aux.Ts_cr
            self.Ps_cr=aux.Ps_cr
            self.Ros_cr=aux.Ros_cr
            self.V_cr=aux.V_cr
            self.k_cr=aux.k_cr
            self.flowdensity_cr=aux.flowdensity_cr
            
            self.flowdensity_thru_G=self.G/self.F
            #вычисление дальнейших параметров бессмысленно, если flowdensity_thru_Ps != flowdensity_thru_G
            while self.was_edited:
                self.was_edited=False
                self.calculate_G_corr()
                self.calculate_G_corr_s()
                self.calculate_capacity()
                self.calculate_capacity_s()
                self.calculate_V()
                self.calculate_V_corr()
                self.calculate_M()
                self.calculate_Force()
                self.calculate_Impulse()
            
    def calculate_thru_FG(self): #расчет с учетом того, что сверхкритическое течение невозможно - в этом случае код выдаст ошибку о том, что поток не проходит сквозь заданное сечение
        if self.is_total_parameters_exist() and not(np.isnan(all(self.mass_comp))):
            #TODO! попробовать сделать так, чтобы алгоритм сам смотрел какие параметры заданы в сrosssection и передавал их внутрь aux без ручного присваивания как сейчас
            aux=IsentropicFlow(self.name_of_parent)
            aux.T=self.T    
            aux.H=self.H
            aux.mass_comp=self.mass_comp
            aux.R=self.R
            aux.P=self.P
            aux.Ro=self.Ro
            aux.Cp=self.Cp
            aux.Cv=self.Cv
            aux.k=self.k
            aux.Sf=self.Sf
            aux.S=self.S
            
            aux.calculate()
            
            self.R=aux.R
            self.P=aux.P
            self.T=aux.T
            self.Ro=aux.Ro
            self.Cp=aux.Cp
            self.Cv=aux.Cv
            self.k=aux.k
            self.H=aux.H
            self.Sf=aux.Sf
            self.S = aux.S
            self.Ts_cr=aux.Ts_cr
            self.Ps_cr=aux.Ps_cr
            self.Ros_cr=aux.Ros_cr
            self.V_cr=aux.V_cr
            self.k_cr=aux.k_cr
            self.flowdensity_cr=aux.flowdensity_cr

            
            if exist(self.G):
                self.calculate_capacity()
                self.calculate_G_corr()
                if exist(self.F):
                    if self.G/self.F >aux.flowdensity_cr:
                        solverLog.error('ERROR! ' + self.name_of_parent + ': calculate_thru_FG: Given masslow cant flow through given area - choked flow. G={G} F={F} P={P} T={T}'.format(G=self.G,F=self.F,P=aux.P,T=aux.T) )
                        raise SystemExit
                    aux.Ts=Ts_thru_GPTHF(self.G,aux.P,aux.T,aux.H,self.F,aux.Ts_cr,aux.mass_comp,aux.R)
                    aux.calculate()
                        
                    self.Ps=aux.Ps
                    self.Ts=aux.Ts
                    self.Ros=aux.Ros
                    self.Cps = aux.Cps
                    self.Cvs = aux.Cvs
                    self.ks = aux.ks
                    self.Hs=aux.Hs
                    self.Sfs=aux.Sfs
                    self.Ss= aux.Ss
                    self.Vsnd=aux.Vsnd
                    self.flowdensity_thru_Ps=aux.flowdensity
                    self.pi = aux.pi
                    self.tau = aux.tau
                    self.q = aux.q
                    self.flowdensity_thru_G=self.G/self.F
                    while self.was_edited:
                        self.was_edited=False
                        self.calculate_G_corr_s()
                        self.calculate_capacity_s()
                        self.calculate_V()
                        self.calculate_V_corr()
                        self.calculate_M()
                        self.calculate_Force()
                        self.calculate_Impulse()
                
    def calculate_totPar_thru_statParV(self): #расчет полных параметров потока на основе заданных статических. возможны как сверхкритика, так и докритика. Плоащдь сечения, расход и сопутствующие параметры не рассчитываются
        if self.is_static_parameters_exist() and self.is_velocity_exist() and not(np.isnan(all(self.mass_comp))):
            aux=IsentropicFlow(self.name_of_parent)
            aux.Ts=self.Ts    
            aux.Hs=self.Hs
            aux.mass_comp=self.mass_comp
            aux.R=self.R
            aux.Ps=self.Ps
            aux.Ros=self.Ros
            aux.Cps=self.Cps
            aux.Cvs=self.Cvs
            aux.ks=self.k
            aux.Sfs=self.Sf
            aux.Ss=self.S
            
            aux.calculate() #дорассчитываем статические параметры
            
            #далее из заданной скорости ищем полные параметры. Скорость может быть задана через V, M или V_corr
            if exist(self.M):
                if self.M==0:
                    self.V=0
                    aux.copy_statPar_to_totPar()
                else:
                    self.V=aux.Vsnd*self.M
                    aux.H=H_thru_HsV(aux.Hs, self.V)
            elif exist(self.V):
                if self.V==0:
                    aux.copy_statPar_to_totPar()
                else:
                    aux.H=H_thru_HsV(aux.Hs, self.V)
            elif exist(self.V_corr):
                if self.V_corr==0:
                    aux.copy_statPar_to_totPar()
                else:
                    aux.T=T_thru_HsTsVcorr(aux.Hs,aux.Ts,self.V_corr,aux.ks,aux.mass_comp,aux.R)
            aux.calculate()
            
            self.R=aux.R
            self.P=aux.P
            self.T=aux.T
            self.Ro=aux.Ro
            self.Cp=aux.Cp
            self.Cv=aux.Cv
            self.k=aux.k
            self.H=aux.H
            self.Sf=aux.Sf
            self.S = aux.S
            self.Ps=aux.Ps
            self.Ts=aux.Ts
            self.Ros=aux.Ros
            self.Cps = aux.Cps
            self.Cvs = aux.Cvs
            self.ks = aux.ks
            self.Hs=aux.Hs
            self.Sfs=aux.Sfs
            self.Ss= aux.Ss
            self.Vsnd=aux.Vsnd
            self.flowdensity_thru_Ps=aux.flowdensity
            self.pi = aux.pi
            self.tau = aux.tau
            self.q = aux.q
            self.Ts_cr=aux.Ts_cr
            self.Ps_cr=aux.Ps_cr
            self.Ros_cr=aux.Ros_cr
            self.V_cr=aux.V_cr
            self.k_cr=aux.k_cr
            self.flowdensity_cr=aux.flowdensity_cr

            while self.was_edited:
                self.was_edited=False
                self.calculate_V_corr()
                self.calculate_M()
                self.calculate_V()
                
    # def calculate_totPar(self): #расчет всех полных параметров по имеющимся данным
    #     if self.is_total_parameters_exist() and not(np.isnan(all(self.mass_comp))):
    #         #TODO! попробовать сделать так, чтобы алгоритм сам смотрел какие параметры заданы в сrosssection и передавал их внутрь aux без ручного присваивания как сейчас
    #         aux.T=self.T    
    #         aux.H=self.H
    #         aux.mass_comp=self.mass_comp
    #         aux.R=self.R
    #         aux.P=self.P
    #         aux.Ro=self.Ro
    #         aux.Cp=self.Cp
    #         aux.Cv=self.Cv
    #         aux.k=self.k
    #         aux.Sf=self.Sf
    #         aux.S=self.S
            
    #         aux.calculate()
            
    #         self.R=aux.R
    #         self.P=aux.P
    #         self.T=aux.T
    #         self.Ro=aux.Ro
    #         self.Cp=aux.Cp
    #         self.Cv=aux.Cv
    #         self.k=aux.k
    #         self.H=aux.H
    #         self.Sf=aux.Sf
    #         self.S = aux.S
    #         self.Ts_cr=aux.Ts_cr
    #         self.Ps_cr=aux.Ps_cr
    #         self.Ros_cr=aux.Ros_cr
    #         self.V_cr=aux.V_cr
    #         self.k_cr=aux.k_cr
    #         self.flowdensity_cr=aux.flowdensity_cr

            

        
        

    
    def status(self):
        for att in dir(self):
            if att[0]!='_' and att[0:9]!='calculate' and att[0:6]!='status' and att[0:10]!='was_edited' and att[0:4]!='copy' and 'aux' not in att and 'exist' not in att:
                print (att,' = ', getattr(self,att)) 
    def copy_attributes(self,other_crosssection): #эта штука нужна для копирования значений элементов, т.к. использование простого присваивания ломает пргргамму изза особенностей языка - в Питоне все переменные - объекты, и они все передаются по ссылке (долго объяснять)
        for key in self.__dict__.keys():
            _temp=getattr(other_crosssection,key)
            if not (type(_temp) == str):
                if not np.all(np.isnan(_temp)): #NB! эта проверка нужна потому, что был прецендент: два последовательных канала. у первого канала на выходе площадь сечения не задается, а на входе во втором канале задается площадь сечения. Соответственно она становится равной площади на выходе из перврго сечения - так сейчас реализован алгоритм: объект crosssection на выходе из узла соответствует такому же объекту на входе в следующий узел. Но в процессе расчета параметров внутри первого узла (объекта channel) происходит копирование атрибутов self.outlet.copy_attributes(self.outlet_ideal) из outlet_ideal в outlet, из-за этого параметр F в outlet затирается
                    setattr(self, key, _temp)
            else:
                setattr(self, key, _temp)

        
#вспомогательные функции:    
def exist(val):
    return not(np.isnan(val))

def not_exist(val):
    return np.isnan(val)
        

            # self.outlet.P=self.outlet_ideal.P
            # self.outlet.H=self.outlet_ideal.H
            # self.outlet.G=self.outlet_ideal.G
            # self.outlet.F=self.outlet_ideal.F
            # self.outlet.mass_comp=self.outlet_ideal.mass_comp
            # self.outlet.V=self.outlet_ideal.V*self.fi
            # self.outlet.Ps=self.outlet_ideal.Ps






# test=CrossSection()
# test.Ps=400000
# test.Ts=400
# test.V_corr=1.5
# # test.P=500000
# # test.T=1000
dry_air_test=np.array([0.7551810473860,0.2314148210000,0.0128814610000,0.0005226706140,0.0000000000000,0.0,0.0]) #массовые доли в сухом воздухе, пруф  ICAO, Manual of the ICAO Standard Atmosphere (extended to 80 kilometres (262 500 feet)), Doc 7488-CD, Third Edition, (1993), ISBN 92-9194-004-6. pg E-x Table B; https://en.wikipedia.org/wiki/Template:Table_composition_of_dry_atmosphere#cite_note-7
# dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00])
# test.mass_comp=dry_air_test
# # test.F=0.01
# # test.G=6.3
# # # test.Ps=400000r
# # # test.Ps_back=200000
# # test.V=500
# # # test.status()
# # test.calculate_thru_FGPback()
# test.calculate_totPar_thru_statParV()
# test.status()

# base=test
# def _test(G,Ps_back):
#     test=copy.deepcopy(base)
#     test.G=G   
#     test.Ps_back=Ps_back
#     test.calculate_thru_FGPback()
#     # test.status()    
#     return test.flowdensity_error

# # # _test(5,300000)



# def _test2(P):
#     test=copy.deepcopy(base)
#     # test.Ps_back=P
#     GGG = optimize.brentq(_test,0.5,20,args=(P,),disp=True)
#     test.G=GGG
#     test.Ps_back=P
#     test.calculate_thru_FGPback()
#     # base.status()
#     return test
    

# rez=_test2(200000)
# rez.status()

# PPP=np.arange(100000,400000,5000)
# xxx=[]

# for P_val in PPP:
#     rez=_test2(P_val)
#     print(P_val)
#     xxx.append(rez)

# XXX=[]
# YYY=[]
# for val in xxx:
#     YYY.append(val.P)
#     XXX.append(val.G)
    
# plt.plot(PPP,XXX)


# test=IsentropicFlow()
# test.P=500000
# test.T=1000
# dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00])
# test.mass_comp=dry_air_test
# # test.Ps=450000
# test.calculate()
# Ps=np.arange(100000.0,499000.0,5000.0 )
# flowdensity=[]
# flowdensity_cr=[]
# for Ps_val in Ps:
#     _test=copy.deepcopy(test)
#     _test.Ps=Ps_val
#     _test.calculate()
#     flowdensity.append(_test.flowdensity)
#     flowdensity_cr.append(_test.flowdensity_cr)

# plt.plot(Ps,flowdensity)
# plt.plot(Ps,flowdensity_cr)

#свойства воздуха и топлива
#dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00])
#print(P2_thru_P1T1T2(500000,500,400,dry_air_test,285.74582159886364))
#print(T2_thru_P1T1P2(500000,500,225334.47437230457,dry_air_test,285.74582159886364,100,1000))
#wet_air_test=np.array([0.749164,0.229674,0.012818,0.000456,0.007888,0,0])
#fuel_test=np.array([0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 1.0000e+00])
#kerosene_air_stoichiometric_combustion_products=np.array([0.7070278421, 0., 0.01209714975, 0.2010579341, 0.07981707402, 0., 0.]) #для керосина и воздуха с условным составом С12H23.325

#print(H(500,dry_air_test))
#print(T_thru_H(200686.4015157996,dry_air_test,200,3000))

#Hu=(2*_H(298.15,coefsCO2,Runiversal)+3*_H(298.15,coefsH2O,Runiversal))-(2*_H(298.15,coefsCH3,Runiversal)+3.5*_H(298.15,coefsO2,Runiversal))/2
#Hukg=Hu/MolW_CH3
#print(Hu)
#R_mix([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00,0])
#TenDoubles = ctypes.c_double * 7
#ii = TenDoubles(7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00, 0.0000e+00)
#
#x=PsTsV_thru_GPTF(1,500000,1000,0.00325383,268497,853,574,dry_air_test,285.74582159886364)
#print(x)
"""
ДАЛЕЕ АЛГОРИТМ ДЛЯ ПРОЕВРКИ ФУНКЦИЙ ГРАИФКАМИ
"""
"""
gas_methan_test=np.array([0.737723,0.151292,0.012622,0.052482,0.045249,0,0,0.000631])
dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00,0])
kerosene_air_stoichiometric_combustion_products=np.array([0.7070278421, 0., 0.01209714975, 0.2010579341, 0.07981707402, 0., 0.]) #для керосина и кислорода с условным составом С12H23.325
#функция вычисления теплоемкости, энтальпии и энтропии продуктов сгорания на основе относительного расхода топлива - упрощенные формулы для CFD
def Cp_products(FAR,L,T):
    rez=(FAR*Cp(T,kerosene_air_stoichiometric_combustion_products)*(1+L)+Cp(T,dry_air_test)*(1-L*FAR))/(FAR+1)
    return rez
def H_products(FAR,L,T):
    rez=(FAR*H(T,kerosene_air_stoichiometric_combustion_products)*(1+L)+H(T,dry_air_test)*(1-L*FAR))/(FAR+1)
    return rez
def S_products(FAR,L,T):
    rez=(FAR*Sf(T,kerosene_air_stoichiometric_combustion_products)*(1+L)+Sf(T,dry_air_test)*(1-L*FAR))/(FAR+1)
    return rez
    

print("проверка")
#print(Rel_humidity(0.0038,100000,273,dry_air_test))
#print(H(500,dry_air_test))
#print(T_thru_H(H(500,dry_air_test),dry_air_test,200,6000))
#print(PsTsV_thru_GPTF(1,500000,1000,0.010158711,dry_air_test))
#print(Ts_thru_GPTF(1,500000,1000,0.00158711,dry_air_test))
#print(Ts_thru_GPTF(1,500000,1000,0.000158711,dry_air_test))
#print(Ts_thru_HM(8000,0.1,dry_air_test,200,6000))
#для проверки строим графики
#test_func=lambda Ts,F: 1-P2_thru_P1T1T2(500000,1000,Ts,dry_air_test)/R_mix(dry_air_test)/Ts*np.sqrt(2*(H(1000,dry_air_test)-H(Ts,dry_air_test)))*F
#Tmatrix2=np.arange(200.0,1000.0,10)
#Pmatrix2=[]
#for Ts in Tmatrix2:
#    Pmatrix2.append(test_func(Ts,0.01))
    
Tmatrix=np.arange(200.0,3000.0,10)
#CpmatrixN2=[]
#CpmatrixO2=[]
#CpmatrixCO2=[]
#CpmatrixAr=[]
#CpmatrixH2O=[]
#CpmatrixJetA=[]
#CpmatrixJetALiquid=[]
CpmatrixAir=[]
CpmatrixCombProdAlfa1=[]
CpmatrixCombProd1=[]
CpmatrixCombProd2=[]
CpmatrixCombProd3=[]
CpmatrixCombProd4=[]
CpmatrixCombProd5=[]
#HmatrixN2=[]
#HmatrixO2=[]
#HmatrixCO2=[]
#HmatrixAr=[]
HmatrixH2O=[]
#HmatrixJetA=[]
#HmatrixJetALiquid=[]
HmatrixAir=[]
HmatrixCombProdAlfa1=[]
HmatrixCombProd1=[]
HmatrixCombProd2=[]
HmatrixCombProd3=[]
HmatrixCombProd4=[]
HmatrixCombProd5=[]
#SmatrixN2=[]
#SmatrixO2=[]
#SmatrixCO2=[]
#SmatrixAr=[]
#SmatrixH2O=[]
#SmatrixJetA=[]
#SmatrixJetALiquid=[]
SmatrixAir=[]
SmatrixCombProdAlfa1=[]
SmatrixCombProd1=[]
SmatrixCombProd2=[]
SmatrixCombProd3=[]
SmatrixCombProd4=[]
SmatrixCombProd5=[]
#test=[]
#kmatrix=[]
#Tsmatrix=[]
#Psmatrix=[]
#Psatmatrix=[]
#Psat2matrix=[]
#Tsmatrix2=[]
#Psmatrix2=[]
#Vmatrix2=[]
#WARmatrix_minus15=[]
#WARmatrix_0=[]
#WARmatrix_15=[]
#WARmatrix_30=[]
#WARmatrix_sat=[]
#RelHum_m=[]

for T in Tmatrix:
#    CpmatrixN2.append(_Cp(T,coefsN2,R_N2))
#    CpmatrixO2.append(_Cp(T,coefsO2,R_O2))
#    CpmatrixCO2.append(_Cp(T,coefsCO2,R_CO2))
#    CpmatrixAr.append(_Cp(T,coefsAr,R_Ar))
#    CpmatrixH2O.append(_Cp(T,coefsH2O,R_H2O))
#    CpmatrixJetA.append(_Cp(T,coefsJetA,R_JetA))
#    CpmatrixJetALiquid.append(_Cp(T,coefsJetA,R_JetA))
    CpmatrixAir.append(Cp(T,dry_air_test))
    CpmatrixCombProdAlfa1.append(Cp(T,kerosene_air_stoichiometric_combustion_products))
    CpmatrixCombProd1.append(Cp_products(0,14.731261494963519,T))
    CpmatrixCombProd2.append(Cp_products(0.02,14.731261494963519,T))
    CpmatrixCombProd3.append(Cp_products(0.04,14.731261494963519,T))
    CpmatrixCombProd4.append(Cp_products(0.06,14.731261494963519,T))
    CpmatrixCombProd5.append(Cp_products(0.08,14.731261494963519,T))
#    HmatrixN2.append(_H(T,coefsN2,R_N2))
#    HmatrixO2.append(_H(T,coefsO2,R_O2))
#    HmatrixCO2.append(_H(T,coefsCO2,R_CO2))
#    HmatrixAr.append(_H(T,coefsAr,R_Ar))
    HmatrixH2O.append(_H(T,coefsH2O,R_H2O))
#    HmatrixJetA.append(_H(T,coefsJetA,R_JetA))
#    HmatrixJetALiquid.append(_H(T,coefsJetA,R_JetA))
    HmatrixAir.append(H(T,dry_air_test))
    HmatrixCombProdAlfa1.append(H(T,kerosene_air_stoichiometric_combustion_products))
    HmatrixCombProd1.append(H_products(0,14.731261494963519,T))
    HmatrixCombProd2.append(H_products(0.02,14.731261494963519,T))
    HmatrixCombProd3.append(H_products(0.04,14.731261494963519,T))
    HmatrixCombProd4.append(H_products(0.06,14.731261494963519,T))
    HmatrixCombProd5.append(H_products(0.08,14.731261494963519,T))
#    SmatrixN2.append(_Sf(T,coefsN2,R_N2))
#    SmatrixO2.append(_Sf(T,coefsO2,R_O2))
#    SmatrixCO2.append(_Sf(T,coefsCO2,R_CO2))
#    SmatrixAr.append(_Sf(T,coefsAr,R_Ar))
#    SmatrixH2O.append(_Sf(T,coefsH2O,R_H2O))
#    SmatrixJetA.append(_Sf(T,coefsJetA,R_JetA))
#    SmatrixJetALiquid.append(_Sf(T,coefsJetA,R_JetA))
    SmatrixAir.append(Sf(T,dry_air_test))
    SmatrixCombProdAlfa1.append(Sf(T,kerosene_air_stoichiometric_combustion_products))
    SmatrixCombProd1.append(S_products(0,14.731261494963519,T))
    SmatrixCombProd2.append(S_products(0.02,14.731261494963519,T))
    SmatrixCombProd3.append(S_products(0.04,14.731261494963519,T))
    SmatrixCombProd4.append(S_products(0.06,14.731261494963519,T))
    SmatrixCombProd5.append(S_products(0.08,14.731261494963519,T))
#    test.append((lambda T,coefs,R: _Cp(T,coefs,R)-1)(T,coefsO2,R_O2))
#    kmatrix.append(k(T,dry_air_test))
#    Psmatrix.append(P2_thru_P1T1T2(500000,3001,T,dry_air_test))

#Pmatrix=np.arange(5000,500000,1000)
#for P in Pmatrix:
#    Tsmatrix.append(T2_thru_P1T1P2(500000,3001,P,dry_air_test,200,3001))
#Fmatrix=np.arange(0.0001,0.02,0.0001)
#for F in Fmatrix:
#    rez=PsTsV_thru_GPTF(1,500000,1000,F,dry_air_test)
#    Tsmatrix2.append(rez[1])
#    Psmatrix2.append(rez[0])
#    Vmatrix2.append(rez[2])
#Tmatrix2=np.arange(200.0,372.0,1)
#for T in Tmatrix2:
#    Psatmatrix.append(P_sat_vapour1(T))
#    Psat2matrix.append(P_sat_vapour2(100000,T))
#    RelHummatrix=np.arange(0.0,2.0,0.05)
#    WARmatrix_sat.append(WAR(1, 100000, T, dry_air_test))
#for RH in RelHummatrix:
#    WARmatrix_minus15.append(WAR(RH, 100000, (273.15-15), dry_air_test))
#    WARmatrix_0.append(WAR(RH, 100000, (273.15), dry_air_test))
#    WARmatrix_15.append(WAR(RH, 100000, (273.15+15), dry_air_test))
#    WARmatrix_30.append(WAR(RH, 100000, (273.15+30), dry_air_test))
#WARmatrix=np.arange(0,0.05,0.001)
#for WARx in WARmatrix:
#    RelHum_m.append(Rel_humidity(WARx,100000,300))

#проверка функций на графике
#print(S_Air(1000)-S_Air(200))
fig, axes = plt.subplots(3,1)
fig.set_size_inches(15, 55)

#axes[0].plot(Tmatrix,CpmatrixN2,label='N2')
#axes[0].plot(Tmatrix,CpmatrixO2,label='O2')
#axes[0].plot(Tmatrix,CpmatrixCO2,label='CO2')
#axes[0].plot(Tmatrix,CpmatrixAr,label='Ar')
#axes[0].plot(Tmatrix,CpmatrixH2O,label='H2O')
#axes[0].plot(Tmatrix,CpmatrixJetA,label='JetA')
#axes[0].plot(Tmatrix,CpmatrixJetALiquid,label='JetALiquid')
axes[0].plot(Tmatrix,CpmatrixAir,label='сухой воздух')
axes[0].plot(Tmatrix,CpmatrixCombProdAlfa1,label='продукты стехиометрического горения керосина q=0,0678828')
axes[0].plot(Tmatrix,CpmatrixCombProd1,'--r',label='продукты горения керосина q=0')
axes[0].plot(Tmatrix,CpmatrixCombProd2,'--y',label='продукты горения керосина q=0.02')
axes[0].plot(Tmatrix,CpmatrixCombProd3,'--g',label='продукты горения керосина q=0.04')
axes[0].plot(Tmatrix,CpmatrixCombProd4,'--b',label='продукты горения керосина q=0.06')
axes[0].plot(Tmatrix,CpmatrixCombProd5,'--c',label='продукты горения керосина q=0.08')
axes[0].legend(fontsize=8)
axes[0].set_xlabel('Температура, К')
axes[0].set_ylabel('Теплоемкость, Дж/кг/К')
axes[0].set_title('Теплоемкость')
#axes[1].plot(Tmatrix,HmatrixN2,label='N2')
#axes[1].plot(Tmatrix,HmatrixO2,label='O2')
#axes[1].plot(Tmatrix,HmatrixCO2,label='CO2')
#axes[1].plot(Tmatrix,HmatrixAr,label='Ar')
axes[1].plot(Tmatrix,HmatrixH2O,label='H2O')
#axes[1].plot(Tmatrix,HmatrixJetA,label='JetA')
#axes[1].plot(Tmatrix,HmatrixJetALiquid,label='JetALiquid')
axes[1].plot(Tmatrix,HmatrixAir,label='сухой воздух')
axes[1].plot(Tmatrix,HmatrixCombProdAlfa1,label='продукты стехиометрического горения керосина q=0,0678828')
axes[1].plot(Tmatrix,HmatrixCombProd1,'--r',label='продукты горения керосина q=0')
axes[1].plot(Tmatrix,HmatrixCombProd2,'--y',label='продукты горения керосина q=0.02')
axes[1].plot(Tmatrix,HmatrixCombProd3,'--g',label='продукты горения керосина q=0.04')
axes[1].plot(Tmatrix,HmatrixCombProd4,'--b',label='продукты горения керосина q=0.06')
axes[1].plot(Tmatrix,HmatrixCombProd5,'--c',label='продукты горения керосина q=0.08')
axes[1].legend(fontsize=8)
axes[1].set_xlabel('Температура, К')
axes[1].set_ylabel('Удельная энтальпия, Дж/кг')
axes[1].set_title('Энтальпия')
#axes[2].plot(Tmatrix,SmatrixN2,label='N2')
#axes[2].plot(Tmatrix,SmatrixO2,label='O2')
#axes[2].plot(Tmatrix,SmatrixCO2,label='CO2')
#axes[2].plot(Tmatrix,SmatrixAr,label='Ar')
#axes[2].plot(Tmatrix,SmatrixH2O,label='H2O')
#axes[2].plot(Tmatrix,SmatrixJetA,label='JetA')
#axes[2].plot(Tmatrix,SmatrixJetALiquid,label='JetALiquid')
axes[2].plot(Tmatrix,SmatrixAir,label='сухой воздух')
axes[2].plot(Tmatrix,SmatrixCombProdAlfa1,label='продукты стехиометрического горения керосина q=0,0678828')
axes[2].plot(Tmatrix,SmatrixCombProd1,'--r',label='продукты горения керосина q=0')
axes[2].plot(Tmatrix,SmatrixCombProd2,'--y',label='продукты горения керосина q=0.02')
axes[2].plot(Tmatrix,SmatrixCombProd3,'--g',label='продукты горения керосина q=0.04')
axes[2].plot(Tmatrix,SmatrixCombProd4,'--b',label='продукты горения керосина q=0.06')
axes[2].plot(Tmatrix,SmatrixCombProd5,'--c',label='продукты горения керосина q=0.08')
axes[2].legend(fontsize=8)
axes[2].set_xlabel('Температура, К')
axes[2].set_ylabel('Удельная энтропия, Дж/кг/К')
axes[2].set_title('Энтропия')
#axes[3].plot(Tmatrix,kmatrix)
#axes[3].set_xlabel('Температура, К')
#axes[3].set_ylabel('Коэффициент адиабаты')
#axes[3].set_title('Коэффициент адиабаты')
#axes[4].plot(Tmatrix,Psmatrix)
#axes[4].set_xlabel('Температура, К')
#axes[4].set_ylabel('Pstat')
#axes[4].set_title('Статическое давление по функции P2_thru_P1T1T2')
#axes[5].plot(Pmatrix,Tsmatrix)
#axes[5].set_xlabel('P2, Pa')
#axes[5].set_ylabel('T2, K')
#axes[5].set_title('Статическая температура по функции T2_thru_P1T1P2')
#lin1=axes[6].plot(Fmatrix,Tsmatrix2,label='Ts')
#axes[6].set_xlabel('F, m2')
#axes[6].set_ylabel('Ts, K')
#axes[6].set_title('Проверка функции PsTsV_thru_GPTF')
#axes[6].set_ylim(bottom=800,top=1100)
#axes2=axes[6].twinx()
#axes2.set_ylabel('Ps, Па')
#lin2=axes2.plot(Fmatrix,Psmatrix2,label='Ps',color='red')
#lines=lin1+lin2
#labs = [l.get_label() for l in lines]
##axes2[6].set_xlabel('F, m2')
#axes[6].legend(lines, labs, loc=0)
#axes2.set_ylim(bottom=250000,top=550000)
#axes[7].plot(Tmatrix2,Psatmatrix,label='wikipedia')
#axes[7].plot(Tmatrix2,Psat2matrix,label='GTP')
#axes[7].set_xlabel('Температура, К')
#axes[7].set_ylabel('Psat')
#axes[7].set_title('Давление насыщенных паров')
#axes[7].legend()
#axes[8].plot(RelHummatrix,WARmatrix_minus15,label='-15')
#axes[8].plot(RelHummatrix,WARmatrix_0,label='0')
#axes[8].plot(RelHummatrix,WARmatrix_15,label='15')
#axes[8].plot(RelHummatrix,WARmatrix_30,label='30')
#axes[8].set_xlabel('Относительная влажность')
#axes[8].set_ylabel('Влагосодержание (удельная влажность), кг пара/ кг сухого воздуха')
#axes[8].set_title('Влажность')
#axes[8].legend()
#axes[9].plot(Tmatrix2,WARmatrix_sat)
#axes[9].set_xlabel('Температура, К')
#axes[9].set_ylabel('Влагосодержание (удельная влажность), кг пара/ кг сухого воздуха')
#axes[9].set_title('Зависимость влагосодержания в воздухе со 100% влажностью от температуры')
#axes[9].legend()
#axes[10].plot(WARmatrix,RelHum_m)
#axes[10].set_xlabel('Влагосодержание')
#axes[10].set_ylabel('отн влажность')
#axes[10].set_title('Зависимость отн влажность от Влагосодержания')




"""
