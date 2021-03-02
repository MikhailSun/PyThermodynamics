# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 15:08:37 2019

@author: Sundukov
"""
import os
import numpy as np
import thermodynamics as td
import copy
#import thermodynamics_c_v1 as td
import pickle
from scipy.interpolate import RectBivariateSpline
from scipy.optimize import brentq
from scipy.optimize import newton
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt
import logging
import ThermoLog
ThermoLog.setup_logger('solverLog', 'info.log',logging.DEBUG)

solverLog=logging.getLogger('solverLog')
dT=0.1
#TODO!!! отревьюить коды узлов
#TODO!!! сделать возможность задавать величину отбора как функцию, зависящую от чего-лиобо, например от приведенных оборотов
#TODO!!! как-то нужно сделать возможность задавать размерность для характеристик турбины и компрессора, чтобы прога сама преобразовывала в нужные ей единицы СИ
#TODO!!! сделать переключатель для масштабирования характеристик компрессора и турбины: чтобы можно было масштабировать либо простым умножением на поправочный коэффициент, либо сначала вычесть единицу, пототм домножить, а поттом снова прибавить единицу
#TODO!!! сделать механизм, который бы обеспечивал невылет расчета если давление в точке подвода больше чем в точке отбора
#TODO!!! нужно бы переделать все узлы через механизм свойств

#класс для описания всех параметров в сечении потока
"""
class CrossSection():
    #!!!НУЖНО ПОРАБОТАТЬ НАД ОПТИМИЗАЦИЕЙ ЭТОГО КЛАССА, ТК ОН ОДИН ИЗ БАЗОВЫХ И К НЕМУ ИДЕТ СОТНИ И ТЫСЯЧИ ОБРАЩЕНИЙ
    #!!!функция должна уметь считать исходя из двух возможных условий: либо расчет ведется исходя из условия недопустимости
    #!!!сверхзвуковой скорости, тогда если известна площадь или пропускная способность, то параметры скорости/расходта и т.п. являются вычисляемыми;
    #!!!либо скорость может быть любой, тьогда вычисляемыми параметрами явлется площадь ис
    #!!! надо в общем подумать, как решить следюущую проблему: если пользователь задаст на входе расход и площадь и при этом поток дозвуковой,
    #!!!то проблем не будет, но в случае сверхзвуковго потока появляется противоречие, т.к. заданный расход не пролезает. Пока не придумал как решить эту проблему,
    #!!! но для стандартных дозвуковых двигателей данная ситуация вроде бы не должна встречаться, нужно только контролировать, чтобы поток не стал сверхзвуковым
    #!!! и прри необходимости выдавать ошибку или предупреждение. Потенциально при расчете вторичных систем мы будем задавать площадь, но не будем задавать расход??? пока непонятно, как быть в этом случае
    def __init__(self):
        #СНАЧАЛА ПЕРЕЧИСОЯЕМ ВСЕ ПАРАМЕТРЫ ИСПОЛЬЗУЕМЫЕ ДЛЯ ОПИСАНИЕ СОСТОЯНИЯ В СЕЧЕНИИ ПОТОКА
        #TODO!! попробовать использовать вместо скалярных значений массив ndarray c одним значением, это нужно для того, чтобы была возможность передавать значения по ссылке. По тестам если использовать массив с одним числом вместо скаляра на быстродействии это скажется только по части записи, чтение по скорости не отдичается. Зато передача параметра по ссылке может придать ускорение в други

        self.was_edited = False #флаг для отслеживания того, была ли структура отредактирована в процессе выполнения метода
        # 1 группа полные параметры газа
        self.P=np.nan
        self.T=np.nan
        self.Ro=np.nan
        # 2 группа статические параметры
        self.Ps=np.nan
        self.Ts=np.nan
        self.Ros=np.nan
        #    Pstatic_real = np.nan
        #    Tstatic_real = np.nan
        #    Rostatic_real = np.nan
        #    Ustatic_real = np.nan
        # 3 группа состав смеси
        self.mass_comp=np.empty(td.Number_of_components) #!!!размер массива должен соответствовать числу составляющих газ
        self.mass_comp[:]=np.nan
        # 4 группа термодинамические параметры смеси
        self.Cp=np.nan
        self.Cps = np.nan
        #    Cpstatic_real = np.nan
        self.Cv=np.nan
        self.Cvs = np.nan
        #    Cvstatic_real = np.nan
        self.R=np.nan
        self.k=np.nan
        self.ks = np.nan
        #    kstatic_real = np.nan
        # 5 группа
        self.H=np.nan
        self.Sf=np.nan
        self.S = np.nan
        # 6 группа
        self.Hs=np.nan
        self.Sfs=np.nan
        self.Ss= np.nan
        #    Hstatic_real = np.nan
        #    Sfstatic_real = np.nan
        #    Sstatic_real = np.nan
        # 7 группа
        self.G=np.nan
        self.G_corr=np.nan #приведенный расход
        self.G_corr_s = np.nan #приведенный расход по статическим параметрам
        #    G_corr_static_real = np.nan //приведенный расход по статическим параметрам
        self.capacity=np.nan #пропускная способность вычисляемая на основе полных параметров, здесь не учитывается эффект запирания потока, если он есть, просто G*T**0.5/P
        self.capacity_s=np.nan #пропускная способность по статическим параметрам, возможное запирание не учитывается
        # self.capacity_thru_Pdownstream=np.nan #пропускная способность на основе давления ниже по потоку, учитывается запирание потока, если оно есть. т.е. расчет по сути соответствует величине газодинамической функции плотности тока q
        self.flowdensity_thru_Ps=np.nan #плотность тока - отношение расхода к площади поперечного сечения
        self.flowdensity_thru_G=np.nan
        #    capacity_static_real = np.nan //пропускная способность по статическим параметрам
        # 8 группа
        #    speed_coef = np.nan //коэффициент скорости
        self.F=np.nan #площадь сечения
        #    Dhydraulic = np.nan //гидравлический диаметр, необходим прежде всего для вычисления числа Рейнольдса
        self.V_corr=np.nan #безразмертная скорость
        self.M=np.nan #число Маха
        self.V=np.nan #скорость
        #    V_corr_real = np.nan #безразмерная скорость
        #    M_real = np.nan #число Маха
        #    V_real = np.nan #скорость
        # 9 группа
        #    Re=np.nan //Рейнольдс
        #    dynamic_viscosity = np.nan //динамическая вязкость
        #    kinematic_viscosity = np.nan //кинематическая вязкость
        # 10 группа газодинамические функции
        self.pi = np.nan 
        self.tau = np.nan
        self.q = np.nan
        # 11 группа
        self.Tref = 288.15 #температура для расчета приведенных параметров
        self.Pref = 101325.0 #давление для расчета приведенных параметров
        # 12 группа критические параметры
        self.Ts_cr=np.nan
        self.Ps_cr=np.nan
        self.Ros_cr=np.nan
        self.V_cr=np.nan
        self.k_cr=np.nan
        self.flowdensity_cr=np.nan
        # 13 параметры импульса и силы от давления в сечении
        self.Force=np.nan
        self.Impulse=np.nan
        
    #ОПРЕДЕЛИМ МЕТОДЫ КЛАССА CrossSection
    def calculate_P(self):
        if np.isnan(self.P):
            a1=not(np.isnan(self.R)) and not(np.isnan(self.T)) and not(np.isnan(self.Ro))
            a2=not(np.isnan(self.T)) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)) and not(np.all(np.isnan(self.mass_comp)))
            if int(a1) + int(a2)>1:
                solverLog.warning('WARNING! calculate_P: Overdetermined source data')
            if a1:
                self.P = self.R*self.T*self.Ro
                self.was_edited = True
            if a2:
                self.P=td.P2_thru_P1T1T2(self.Ps,self.Ts,self.T,self.mass_comp,self.R)
                self.was_edited = True
    def calculate_T(self):
        if np.isnan(self.T):
            a1=not(np.isnan(self.R)) and not(np.isnan(self.P)) and not(np.isnan(self.Ro))
            a2=not(np.isnan(self.H)) and not(np.all(np.isnan(self.mass_comp)))
            if int(a1) + int(a2)>1:
                solverLog.warning('WARNING! calculate_T: Overdetermined source data')
            if a1: #ищем температуру из P/Ro=R*T
                self.T = self.P / self.Ro / self.R
                self.was_edited = True
            if a2:
                self.T=td.T_thru_H(self.H,self.mass_comp,200,3000)
                self.was_edited = True
    def calculate_Ro(self):
        if np.isnan(self.Ro) and not(np.isnan(self.R)) and not(np.isnan(self.P)) and not(np.isnan(self.T)): #ищем плотность из P/Ro=R*T
            self.Ro = self.P / self.R / self.T
            self.was_edited = True
    def calculate_Ts_cr(self):
        if np.isnan(self.Ts_cr) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.Ts_cr=td.Critical_Ts(self.T,self.mass_comp,self.R)
            self.was_edited = True
    def calculate_Ps_cr(self):
        if np.isnan(self.Ps_cr) and not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.isnan(self.Ts_cr)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.Ps_cr=td.P2_thru_P1T1T2(self.P,self.T,self.Ts_cr,self.mass_comp,self.R)
            self.was_edited = True
    def calculate_Ros_cr(self):
        if np.isnan(self.Ros_cr) and not(np.isnan(self.Ps_cr)) and not(np.isnan(self.Ts_cr)) and not(np.isnan(self.R)):
            self.Ros_cr=self.Ps_cr/self.Ts_cr/self.R
            self.was_edited = True
    def calculate_Ps(self):
        if np.isnan(self.Ps):
            if not(np.isnan(self.R)) and not(np.isnan(self.Ts)):
                a1=not(np.isnan(self.P)) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp)))
                a2=not(np.isnan(self.Ros))
                if int(a1) + int(a2)>1:
                    solverLog.warning('WARNING! calculate_Ps: Overdetermined source data')
                if a1: #ищем давление через энтропию, дельта энтропии = 0
                    self.Ps = td.P2_thru_P1T1T2(self.P, self.T, self.Ts, self.mass_comp,self.R)
                    self.was_edited = True
                elif a2: #ищем давление из P/Ro=R*T
                    self.Ps = self.R*self.Ts*self.Ros
                    self.was_edited = True
#                elif not(np.isnan(self.Us)): #ищем давление из P/Ro=R*T
#                    self.Ps = self.R*self.Ts / self.Us
#                    self.was_edited = True
    def calculate_Ts(self):
        if np.isnan(self.Ts): #ищем температуру из P/Ro=R*T или из H=Hстатика+V^2/2
            a1=not(np.isnan(self.Ros)) and not(np.isnan(self.Ps)) and not(np.isnan(self.R))
            a2=not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.Ps)) and not(np.isnan(self.R))
            a3=not(np.isnan(self.Hs)) and not(np.all(np.isnan(self.mass_comp)))
            a4=not(np.isnan(self.M)) and not(np.isnan(self.H)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R))
            # a5=not(np.isnan(self.G)) and not(np.isnan(self.P)) and not(np.isnan(self.T)) and not(np.isnan(self.F)) and not(np.isnan(self.Ps_cr)) and not(np.isnan(self.Ts_cr)) and not(np.isnan(self.V_cr)) and not(np.isnan(self.R))
            if int(a1) + int(a2) + int(a3) + int(a4)>1:
                solverLog.warning('WARNING! calculate_Ts: Overdetermined source data')
            if a1:
                self.Ts = self.Ps / self.Ros / self.R
                self.was_edited = True
            elif a2:
                self.Ts=td.T2_thru_P1T1P2(self.P,self.T,self.Ps,self.mass_comp,self.R,200,self.T+dT)#изначально была эта формула, но при расчете невязки на сопле бывает ситуация, когда статика во время итераций больше полоного давления, из-за этого эта формула крашится (т.к. Ts будет больше Т). Чтобы этого избежать, пробуем указать перхний диапазон по Т 2000
                # self.Ts=td.T2_thru_P1T1P2(self.P,self.T,self.Ps,self.mass_comp,self.R,200,2000)
                self.was_edited = True
          # elif not(np.isnan(self.Us)):
          #     self.Ts = self.Ps * self.Us / self.R
          #     self.was_edited = True
            elif a3:
                self.Ts = td.T_thru_H(self.Hs, self.mass_comp,200,self.T+dT)
                self.was_edited = True
            elif a4:
                self.Ts = td.Ts_thru_HM(self.H, self.M, self.mass_comp, self.R, 200, 2500)
                self.was_edited = True
            else:
                self.calculate_Ts_thru_FPT()
            # использование этой части ниже нежелательно, т.к. она считает только в области до критического перепада, иначе выдает ошибку - это вносит серьезную неустойчивость в расчет
            # elif a5: 
            #     self.Ts = td.Ts_thru_GPTF(self.G,self.P,self.T,self.F,self.mass_comp,self.R)
            #     self.was_edited = True
    def calculate_Ts_thru_FPT(self): #вынесено отдельной строкой, т.к. здесь будет учитываться эффект максимальной возможной пропускной способности
        if np.isnan(self.Ts) and not(np.isnan(self.flowdensity_thru_G)) and not(np.isnan(self.flowdensity_cr)) and not(np.isnan(self.F)):
            if self.flowdensity_thru_G < self.flowdensity_cr:
                if  not(np.isnan(self.G)) and not(np.isnan(self.P)) and not(np.isnan(self.T)) and not(np.isnan(self.H)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
                    self.Ts=td.Ts_thru_GPTHF(self.G,self.P,self.T,self.H,self.F,self.Ts_cr,self.mass_comp,self.R)
                    self.was_edited = True
            else:
                if not(np.isnan(self.Ts_cr)):
                    self.Ts=self.Ts_cr
                    self.was_edited = True
    def calculate_Ros(self):
    	if np.isnan(self.Ros): #ищем плотность из P/Ro=R*T или G=Ro*V*F
            a2=not(np.isnan(self.R)) and not(np.isnan(self.Ps)) and not(np.isnan(self.Ts))
            # a1=not(np.isnan(self.G)) and not(np.isnan(self.V)) and not(np.isnan(self.F)) and self.V!=0 and np.isnan(self.Ps)
            # if int(a1) + int(a2)>1:
            #     solverLog.warning('WARNING! calculate_Ros: Overdetermined source data')
            if a2:
                self.Ros = self.Ps / self.R / self.Ts
                self.was_edited = True
            # elif a1:
            #     self.Ros = self.G / self.V / self.F
            #     self.was_edited = True

    def calculate_Cp(self):
        if np.isnan(self.Cp) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))):
            self.Cp = td.Cp(self.T, self.mass_comp)
            self.was_edited = True
    def calculate_Cv(self):
        if np.isnan(self.Cv) and not(np.isnan(self.k)) and not(np.isnan(self.Cp)):
            self.Cv = self.Cp / self.k
            self.was_edited = True
    def calculate_k(self):
        if np.isnan(self.k) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.k = td.k(self.T, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_k_cr(self):
        if np.isnan(self.k_cr) and not(np.isnan(self.Ts_cr)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.k_cr = td.k(self.Ts_cr, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_Cps(self):
        if np.isnan(self.Cps) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))):
            self.Cps = td.Cp(self.Ts, self.mass_comp)
            self.was_edited = True
    def calculate_Cvs(self):
        if np.isnan(self.Cvs) and not(np.isnan(self.Cps)) and not(np.isnan(self.ks)):
            self.Cvs = self.Cps / self.ks
            self.was_edited = True
    def calculate_ks(self):
        if np.isnan(self.ks) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.ks = td.k(self.Ts, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_R(self):
        if np.isnan(self.R) and not(np.all(np.isnan(self.mass_comp))):
            self.R = td.R_mix(self.mass_comp)
            self.was_edited = True
    def calculate_H(self):
        if np.isnan(self.H):
            a1=not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp)))
            a2=not(np.isnan(self.Hs)) and not(np.isnan(self.V))
            if int(a1) + int(a2)>1:
                solverLog.warning('WARNING! calculate_H: Overdetermined source data')
            if a1:
                self.H = td.H(self.T, self.mass_comp)
                self.was_edited = True
            if a2:
                self.H=self.Hs+self.V*self.V/2
                self.was_edited = True
    def calculate_Sf(self):
        if np.isnan(self.Sf) and not(np.isnan(self.T)) and not(np.all(np.isnan(self.mass_comp))):
            self.Sf = td.Sf(self.T, self.mass_comp)
            self.was_edited = True
    def calculate_S(self):
        if np.isnan(self.S) and not(np.isnan(self.T)) and not(np.isnan(self.P)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.S = td.S(self.P,self.T,self.mass_comp,self.R)
            self.was_edited = True
    def calculate_Hs(self):
        if np.isnan(self.Hs):
            a1=not(np.isnan(self.H)) and not(np.isnan(self.V))
            a2=not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp)))
            if int(a1) + int(a2)>1:
                solverLog.warning('WARNING! calculate_Hs: Overdetermined source data')
            if a1:
                self.Hs = self.H - self.V*self.V / 2
                self.was_edited = True
            elif a2:
                self.Hs = td.H(self.Ts, self.mass_comp)
                self.was_edited = True
    def calculate_Sfs(self):
        if np.isnan(self.Sfs) and not(np.isnan(self.Ts)) and not(np.all(np.isnan(self.mass_comp))):
            self.Sfs = td.Sf(self.Ts, self.mass_comp)
            self.was_edited = True
    def calculate_Ss(self):
        if np.isnan(self.Ss) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)) and not(np.all(np.isnan(self.mass_comp))) and not(np.isnan(self.R)):
            self.Ss = td.S(self.Ps, self.Ts, self.mass_comp, self.R)
            self.was_edited = True
    def calculate_flowdensity_thru_Ps(self):
        if np.isnan(self.flowdensity_thru_Ps):
            if not(np.isnan(self.M)) and not(np.isnan(self.Ts)) and not(np.isnan(self.ks)) and not(np.isnan(self.R)) and not(np.isnan(self.Ps)):
                self.flowdensity_thru_Ps=self.M*self.Ps*np.sqrt(self.ks/self.R/self.Ts)
                self.was_edited = True  
    def calculate_flowdensity_thru_G(self):
        if np.isnan(self.flowdensity_thru_G):
            if not(np.isnan(self.G)) and not(np.isnan(self.F)):
                self.flowdensity_thru_G=self.G/self.F
                self.was_edited = True
    def calculate_capacity(self):
        if np.isnan(self.capacity) and not(np.isnan(self.G)) and not(np.isnan(self.T)) and not(np.isnan(self.P)):
            self.capacity = self.G*np.sqrt(self.T) / self.P
            self.was_edited = True
    # def calculate_capacity_thru_Pdownstream(self):
    #     if np.isnan(self.capacity_thru_Pdownstream) and not(np.isnan(self.M)) and not(np.isnan(self.ks)) and not(np.isnan(self.R)) and not(np.isnan(self.tau)) and not(np.isnan(self.pi)):
    #         self.capacity_thru_Pdownstream=self.M*(self.ks/self.R/self.tau)**0.5*(self.pi)
    #         self.was_edited = True
    def calculate_capacity_s(self):
        if np.isnan(self.capacity_s) and not(np.isnan(self.G)) and not(np.isnan(self.Ts)) and not(np.isnan(self.Ps)):
            self.capacity_s = self.G*np.sqrt(self.Ts) / self.Ps
            self.was_edited = True
    def calculate_flowdensity_cr(self):
        if np.isnan(self.flowdensity_cr) and not(np.isnan(self.Ts_cr)) and not(np.isnan(self.Ps_cr)) and not(np.isnan(self.k_cr)) and not(np.isnan(self.R)):
            self.flowdensity_cr = np.sqrt(self.k_cr/self.R/self.Ts_cr)*self.Ps_cr
            self.was_edited = True
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
    def calculate_V_cr(self):
        if np.isnan(self.V_cr) and not(np.isnan(self.Ts_cr)) and not(np.isnan(self.R)) and not(np.all(np.isnan(self.mass_comp))):
            self.V_cr=np.sqrt(td.k(self.Ts_cr,self.mass_comp,self.R)*self.R*self.Ts_cr)
            self.was_edited = True
    def calculate_V(self):
        if (np.isnan(self.V)):
            #TODO! бывают ситуации, когда параметр можно вычислить разными способами, т.е. есть различные наборы данных, позволяющих вычислить этот параметр, нужно как-то это учесть. Как - пока не придумал:(
            a1=not(np.isnan(self.G)) and not(np.isnan(self.Ros)) and not(np.isnan(self.F)) and np.isnan(self.Ps) and np.isnan(self.Ts) 
            a2=not(np.isnan(self.T)) and not(np.isnan(self.V_corr)) and not(np.isnan(self.R)) and not(np.all(np.isnan(self.mass_comp)))
            a3=not(np.isnan(self.M)) and not(np.isnan(self.Ts)) and not(np.isnan(self.ks)) and not(np.isnan(self.R))
            a4=not(np.isnan(self.H)) and not(np.isnan(self.Hs))
            if int(a1) + int(a2)+int(a4)>1:
                solverLog.warning('WARNING! calculate_V: Overdetermined source data')
            if a2:
                self.V = self.V_cr*self.V_corr
                self.was_edited = True
            elif a3:
                Vsnd=np.sqrt(self.ks*self.R*self.Ts)
                self.V = self.M*Vsnd
                self.was_edited = True
            elif a4:
                self.V=np.sqrt(2*(self.H-self.Hs))
                self.was_edited = True
            elif a1:
                self.V = self.G / self.Ros / self.F
                self.was_edited = True
    def calculate_V_corr(self):
        if np.isnan(self.V_corr) and not(np.isnan(self.V)) and not(np.isnan(self.V_cr)):
            self.V_corr=self.V/self.V_cr
            self.was_edited = True
    def calculate_F(self):
        if np.isnan(self.F) and not(np.isnan(self.G)) and not(np.isnan(self.Ros)) and not(np.isnan(self.V)):
            self.F = self.G / self.Ros / self.V
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
        if np.isnan(self.q) and not(np.isnan(self.Ros_cr)) and not(np.isnan(self.Ros)) and not(np.isnan(self.V)) and not(np.isnan(self.V_cr)):
            self.q = self.Ros*self.V / self.Ros_cr / self.V_cr
            self.was_edited = True
    def calculate_M(self):
        if np.isnan(self.M) and not(np.isnan(self.V)) and not(np.isnan(self.Ts)) and not(np.isnan(self.R)) and not(np.isnan(self.ks)):
            Vsnd=np.sqrt(self.ks*self.R*self.Ts)
            self.M = self.V / Vsnd
            self.was_edited = True
    def calculate_Force(self):
        if np.isnan(self.Force) and not(np.isnan(self.Ps)) and not(np.isnan(self.F)):
            self.Force=self.Ps*self.F
            self.was_edited = True
    def calculate_Impulse(self):
        if np.isnan(self.Impulse) and not(np.isnan(self.G)) and not(np.isnan(self.V)):
            self.Impulse=self.G*self.V
            self.was_edited = True
            
    def calculate(self): #расчет всех параметров при наличии возможности
        #TODO?!! организовать проверку на наличие исходных данных, чтобы в случае их отсутствия выдавалось предупреждение - чо?!
        #!!! сейчас сделано так, что если в исходных данных есть Ps иили Ts, то величина G в исходных данных игнорируется
        self.was_edited = False
        #1 группа параметров: сначала проверим значения P T Ro и U. Все рассчитывается из уравнения P/Ro=R*T
        self.calculate_P()
        self.calculate_T()
        self.calculate_Ro()
       #2 группа параметров
        self.calculate_Ts()
        self.calculate_Ros()
        self.calculate_Ps()
#        calculate_Pstatic_real()
#        calculate_Tstatic_real()
#        calculate_Rostatic_real()
#        calculate_Ustatic_real()
        #4 группа параметров: теплоемкости, коэф адиабаты, газовая постоянная, относительная влажность
        self.calculate_Cp()
        self.calculate_k()
        self.calculate_Cv()
        self.calculate_Cps()
        self.calculate_ks()
        self.calculate_Cvs()
#        calculate_Cpstatic_real()
#        calculate_Cvstatic_real()
#        calculate_kstatic_real()
        self.calculate_R()
#        calculate_Humidity()
#        calculate_WAR()
        #5 группа: вычисление полных энтальпии, вспомогательной функции энтропии и энтропии
        self.calculate_H()
        self.calculate_Sf()
        self.calculate_S()
        #6 группа: вычисление статических энтальпии, вспомогательной функции энтропии и энтропии
        self.calculate_Hs()
        self.calculate_Sfs()
        self.calculate_Ss()
#        calculate_Hstatic_real()
#        calculate_Sfstatic_real()
#        calculate_Sstatic_real()
        #7 группа: вычисление расходов и пропускной способности
        self.calculate_G() 
        self.calculate_G_corr()
        self.calculate_G_corr_s()
#        calculate_G_relative_static_real();
        self.calculate_flowdensity_thru_Ps()
        self.calculate_flowdensity_thru_G()
        self.calculate_capacity()
        self.calculate_capacity_s()
        # self.calculate_capacity_thru_Pdownstream()
#        calculate_capacity_static_real();
        #8 группа поиск площади сечения, безразмерной скорости лямбда, числа Маха и физической скорости (м/с)
        self.calculate_F()
        self.calculate_V_corr()
        self.calculate_M()
        self.calculate_V()
#        calculate_V_real()
#        calculate_lambda_real();
#        calculate_M_real();
        #9 группа параметров: коэффициенты динамической и кинематической вязкости, критерии Рейнольдса автоматический не вычисляется, т.к. он зависит от формы канала, т.е. при необходимости его нужно считать вручную
#        calculate_viscosity()
#        calculate_Re();
        #10 группа газодинамические функции Пи, Тау и Ку
        self.calculate_pi()
        self.calculate_tau()
        self.calculate_q()
        # 12 группа критические параметры
        self.calculate_Ts_cr()
        self.calculate_Ps_cr()
        self.calculate_Ros_cr()
        self.calculate_V_cr()
        self.calculate_k_cr()
        self.calculate_flowdensity_cr()
        # 13 тяга и импульс
        self.calculate_Force()
        self.calculate_Impulse()
        if (self.was_edited):
            self.calculate()
    def status(self):
#        rez={'was_edited':self.was_edited, 'P':self.P, 'T':self.T, 'Ro':self.Ro, 'U':self.U, 'Ps':self.Ps, 'Ts':self.Ts, 'Ros':self.Ros, 'Us':self.Us, 'mass_comp':self.mass_comp, 
#             'Cp':self.Cp, 'Cps':self.Cps, 'Cv':self.Cv, 'Cvs':self.Cvs, 'R':self.R, 'k':self.k, 'ks':self.ks, 'H':self.H, 'Sf':self.Sf, 'S':self.S, 'Hs':self.Hs, 'Sfs':self.Sfs, 'Ss':self.Ss,
#             'G':self.G, 'G_corr':self.G_corr, 'G_corr_s':self.G_corr_s, 'Capacity':self.capacity, 'Capacity_s':self.capacity_s, 'F':self.F, 'Lambda':self.V_corr, 'M':self.M, 'V':self.V,
#             'pi':self.pi, 'tau':self.tau, 'q':self.q}
        for att in dir(self):
            if att[0]!='_' and att[0:9]!='calculate' and att[0:6]!='status' and att[0:10]!='was_edited' and att[0:4]!='copy':
                print (att,' = ', getattr(self,att)) 
    
    def copy_attributes(self,other_crosssection): #эта штука нужна для копирования значений элементов, т.к. использование простого присваивания ломает пргргамму изза особенностей языка - в Питоне все переменные - объекты, и они все передаются по ссылке (долго объяснять)
        for key in self.__dict__.keys():
            setattr(self, key, getattr(other_crosssection,key))
"""

# test=td.CrossSection('жопа')
# test.P=500000
# test.T=1000
# test.Ps_back=400000
# dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00])
# test.mass_comp=dry_air_test
# test.F=0.08
# test.G=50
# test.calculate_thru_FGPback()

# test2=td.CrossSection()
# test2.P=500000
# test2.T=1000
# # dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00])
# test2.mass_comp=dry_air_test
# test2.F=0.08
# test2.G=50
# test2.calculate_thru_FG()

#проверяем что класс crosssectioin работает как надо
#dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00])      
#test=CrossSection()
#test.status()
#test.mass_comp=dry_air_test
#test.P=100000
#test.T=573
#test.G=39
#test.F=45
#test.calculate()
#print('calculating..........')
#test.status()

#ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ, КОТОРАЯ ИЗВЛЕКАЕТ ИЗ МАССИВА INITIAL_DATA НУЖНОЕ ЗНАЧЕНИЕ

#class extract(): #этот класс нужен для извлечения различных функций, которые может задавать пользователь, например, для характеристики потерь давления в канале через массив initial_data
#    def __init__(self, function, *list_of_parameters): #инициализация происходит путем задания внешней функции function и передачи списка с текстовым обозначением используемых аргументов. Наименования аргументов должны точно соответствовать используемым внутри классов узлов (т.е. например PRtt или n_phys), если параметр касается не в целом всего узла, а его входного или выходного сечения, или горла СА, то нужно перед названием параметра указать это сечение через тире (например, inlet-G_core или outlet-V_corr или throttle-...)
#        if not callable(function):
#            self.func_obj=lambda x:function #TODO! некрасиво! надо убрать x, он не используется
#        else:
#            self.func_obj=function
#        
#        self.list_of_param=list_of_parameters
#        self.array_of_param=np.empty(len(list_of_parameters))
#        self.device=np.nan
#    def check_parameters(self,device): #здесь проверяем, что указанные в списке list_of_parameters параметры присутствуют у данного узла, если их нет - сообщаем об ошибке
#        if len(self.list_of_param)>0:
#            for param in self.list_of_param:
#                link=device
#                if '-' in param: #смотрим, есть ли в обозначении параметра дефис, если есть, значит это "сложный" параметр ссылающийся либо на чеение внутри узла, либо на другой узел
#                    _param=param.split('-')
#                    for element in _param:
#                        if hasattr(link,element):
#                            link=getattr(link,element)
#                        else:
#                            print('При проверке пользовательской функции в узле '+device.name+' не найден параметр '+param) 
#                            raise SystemExit
#                else:
#                    if not hasattr(device,param):
#                        print('При проверке пользовательской функции в узле '+device.name+' не найден параметр '+param) 
#                        raise SystemExit           
#        self.device=device
#    def calculate(self):
#        for i, param in enumerate(self.list_of_param):
#            link=self.device
#            if '-' in param: #смотрим, есть ли в обозначении параметра наименование сечения узла
#                _param=param.split('-')
#                for element in _param:
#                    link=getattr(link,element)
#            else:
#                link=getattr(self.device,param)
#            self.array_of_param[i]=link
##        print(self.device.name)
##        print(self.func_obj)
##        type(self.func_obj)
#        if self.array_of_param.size==1:
#            _parameters=self.array_of_param[0]
#        else:
#            _parameters=self.array_of_param
#        return self.func_obj(_parameters)
    
#вспомогательная по сути пустая функция (класс точнее), иногда нужна чтобы возвращать значения по умолчанию
class default_function():
    def __init__(self,arg):
        self.rezult=arg
    def calculate(self):
        return self.rezult
    def check_parameters(self,device):
        pass
    
            
#КЛАССЫ УЗЛОВ ДВИГАТЕЛЯ

class Compressor():
    def __init__(self, initial_data, upstream, engine, name):
        self.name=name
#        id_names.append(name)
#        id_links.append(self)
        engine.devices[name] = self
        self.variable_guide_vanes=initial_data.get((name+'.variable_guide_vanes'),False) #параметр, который говорит о том, будут ли использоваться поворотные направляющие аппараты. Если да, то алгоритм ожидает дополнительный варьируемый параметр - угол поворота НА и несколько характеристик компрессора, соответствующих различным углам НА
        self.rotor=int(initial_data[name+'.rotor']) #номер ротора (этот номер должен быть согласован с другими узлами ГТД на этом же роторе, т.е. узлы (турбина) на одном роторе имеют один номер ротора). номер ротора должен начинаться от 1 (не 0!). Все ротора должны иметь последовательные номера в порядке возрастания от 1.
        self.name_of_n='n'+str(self.rotor)
        self.name_of_betta=name+'_betta'
        self.name_of_G_error=name+'_G'
        self.name_of_N_error=self.name_of_n+'_dN'
        self.name_of_angle=name+'_angle'
        engine.arguments[self.name_of_n]=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий обороты 
        engine.arguments[self.name_of_betta]=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий вспомогательную переменную бетта для расчета характеристики

        if self.variable_guide_vanes==True:
            #TODO!!! Временный костыль!!! убоать! 
            if engine.name_of_engine=='GTE-170':
                engine.arguments[self.name_of_angle]=np.nan
            #TODO!!! Временный костыль!!! убоать! 
            
#        self.id=len(id_names)-1
        self.upstream=upstream
        self.inlet=upstream.outlet
        self.outlet=td.CrossSection(self.name)
        
        _F=initial_data.get((name+'.F_inlet'),np.nan)
        if ~np.isnan(self.inlet.F) and ~np.isnan(_F):
            print('В узлах %s и %s конфликт площадей: %.3f и %.3f' % (self.name,self.upstream.name,_F,self.inlet.F))
            raise SystemExit
        elif np.isnan(self.inlet.F) and ~np.isnan(_F):
            self.inlet.F=_F
        self.outlet.F=initial_data.get((name+'.F_outlet'),np.nan)
        
        self.n_phys=np.nan #физические обороты ротора
        self.n_corr=np.nan#приведенные обороты ротора
        self.PRtt=np.nan#степень повышения полного давления
        self.PRts=np.nan#степень повышения статического давления на выходе
        self.L=np.nan#удельная работа
        self.Efftt=np.nan#кпд
        self.Effts=np.nan#кпд по статическим параметрам на выходе
        self.N=np.nan#мощность компрессора
        self.dKy=np.nan#запас газодинамической устойчивости
        self.betta=np.nan#вспомогательная переменная, характеризующая положение расчетной точки на характеристике. Ее нормальное значение от 0 до 1, допускаются небольшие отклонения, которые говорят о том, что расчет идет в области экстраполяции, т.е. с низкой точностью
        self.angle=np.nan
        self.Re=np.nan
        #коэффициенты А - искусственные поправочные коэффициенты к характеристикам
        self.A_G_ncorr=initial_data.get((name+'.A_G_ncorr'),default_function(1))
        self.A_G_ncorr.check_parameters(self) #TODO! подумать, как можно сделать так, чтобы объединить эту строку и выше одним методом. Т.е. предыдущая строка извлекает указатель на функцию из массива исходных данных, а эта - передает ему в качестве аргумента доп информацию - указатель на данный экземпляр класса, который заранее неизвестен.
        self.A_PR_ncorr=initial_data.get(name+'.A_PR_ncorr',default_function(1))
        self.A_PR_ncorr.check_parameters(self)
        self.A_Eff_ncorr=initial_data.get(name+'.A_Eff_ncorr',default_function(1))
        self.A_Eff_ncorr.check_parameters(self)
        
        self.A_G_Re=initial_data.get((name+'.A_G_Re'),default_function(1))
        self.A_G_Re.check_parameters(self)
        self.A_PR_Re=initial_data.get((name+'.A_PR_Re'),default_function(1))
        self.A_PR_Re.check_parameters(self)
        self.A_Eff_Re=initial_data.get((name+'.A_Eff_Re'),default_function(1))
        self.A_Eff_Re.check_parameters(self)
        
        self.A_G_ncorr_value=np.nan
        self.A_PR_ncorr_value=np.nan
        self.A_Eff_ncorr_value=np.nan
        self.A_G_Re_value=np.nan
        self.A_PR_Re_value=np.nan
        self.A_Eff_Re_value=np.nan
        
        #для увязки
        self.ident_G_value=initial_data.get('ident.'+name+'.G',1.0)
        self.ident_PR_value=initial_data.get('ident.'+name+'.PR',1.0)
        self.ident_Eff_value=initial_data.get('ident.'+name+'.Eff',1.0)
        self.ident_n_value=initial_data.get('ident.'+name+'.n',1.0)
        
        self.T_inlet_design_point=initial_data[name+'.T_inlet_dp']#температура на входе в расчетной точке (т.е. на режиме, на котором проводилось проектирование компрессора)
        self.P_inlet_design_point=initial_data[name+'.P_inlet_dp']#авление на входе в расчетной точке (т.е. на режиме, на котором проводилось проектирование компрессора)
        
         #TODO!!! Временный костыль!!! убоать! 
        if engine.name_of_engine!='GTE-170':
            self.G_map=initial_data[name+'.G_map']
            self.PR_map=initial_data[name+'.PR_map']
            self.Eff_map=initial_data[name+'.Eff_map']
        else:
            with open(os.getcwd()+'/'+'maps/GTE-170/2020_11_12_compr_var1/GTE170 Compressor CFD 2020_11.dat', 'rb') as f:
                data_map = pickle.load(f)
            Gminus3=data_map['Gminus3']
            Gplus168=data_map['Gplus168']
            Gplus30=data_map['Gplus30']
            PRminus3=data_map['PRminus3']
            PRplus168=data_map['PRplus168']
            PRplus30=data_map['PRplus30']
            Effminus3=data_map['Effminus3']
            Effplus168=data_map['Effplus168']
            Effplus30=data_map['Effplus30']
            
            def G_map(n,betta,angle):
                x_angle=np.array([3.0,-13.8,-30.0])
                y_G=np.array([Gminus3(n,betta)[0][0],Gplus168(n,betta)[0][0],Gplus30(n,betta)[0][0]])
                G_f=np.poly1d(np.polyfit(x_angle,y_G,2))
                _angle=3.0 if angle>3.0 else (-30.0 if angle<-30.0 else angle)
                return G_f(_angle)
            self.G_map=G_map
            
            def PR_map(n,betta,angle):
                x_angle=np.array([3.0,-13.8,-30.0])
                y_PR=np.array([PRminus3(n,betta)[0][0],PRplus168(n,betta)[0][0],PRplus30(n,betta)[0][0]])
                PR_f=np.poly1d(np.polyfit(x_angle,y_PR,2))
                _angle=3.0 if angle>3.0 else (-30.0 if angle<-30.0 else angle)
                return PR_f(_angle)
            self.PR_map=PR_map

            def Eff_map(n,betta,angle):
                x_angle=np.array([3.0,-13.8,-30.0])
                y_Eff=np.array([Effminus3(n,betta)[0][0],Effplus168(n,betta)[0][0],Effplus30(n,betta)[0][0]])
                Eff_f=np.poly1d(np.polyfit(x_angle,y_Eff,2))
                _angle=3.0 if angle>3.0 else (-30.0 if angle<-30.0 else angle)
                return Eff_f(_angle)
            self.Eff_map=Eff_map
        #TODO!!! Временный костыль!!! убоать! 
            
        
        self.G_corr_map_calc=np.nan
        self.G_corr_error=np.nan
        
#        self.G_inlet_corr_map=np.nan #попробуем не использовать невязку по приведенному расходу между расчетной венличиной и характеристикой
        initial_data['amount_of_rotors'].add(self.rotor)
        initial_data['amount_of_betta']+=1
        self.betta_id=initial_data['amount_of_betta']
                
    def calculate(self,engine):
        #!!!ввести проверку на наличие необходимого минимума данных для начала расчета
        """
        Проверяем необходимый минимум данных
        rotor - номер_ротора - из массива варьируемых переменных
        Gвхода - из предыдущего узла
        dp(T P) - исх данные
        G_map, PR_map, Eff_map - исх данные
            - предварительно считаем данные по характеристикам PR, Gпр, кпд
        Pвх и Tвх - предыдущий узел, если этих данных нет, то Pвх и Tвх приравниваем в первом приближении тому, что задано на входе в предыдущий узел, вычисляем Gфиз, запускаем на расчет предыдущий узел)
            - основной расчет
            - передача данных к следующему узлу и расчет его
        """
#        self.inlet.calculate() #по возможности уточняем уже известные параметры если для этого достаточно данных
        
        #считаем условное число Рейнольдса, чтобы на его основе считтаь поправочные коэффициенты к характеристикам
        self.Re=self.inlet.P*0.1019716/(self.inlet.T**1.254) #0.1019716 - это перевод из Па в кгс/м**2, тк в оригинальной формуле из методики климова так
        self.n_phys=engine.arguments[self.name_of_n] #массив variables будет построен по следующей схеме {0)Th,1)Ph,2)Humidity, 3)Mach number,4)Ginlet,5)Gfuel,6)n1,...,nx, x)betta...}
        self.n_corr=self.n_phys*np.sqrt(self.T_inlet_design_point/self.inlet.T)#для расчета характеристик вычисляем приведенные обороты на основе заданных физических
        
#        _func=lambda _betta: self.inlet.G_corr-self.A_G_corr*float(self.G_map(n_corr_corrected,_betta))
#        self.betta=brentq(_func,-0.5,1.5,disp=True)
#        self.betta=newton(_func,0.5)
        self.betta=engine.arguments[self.name_of_betta]
        if self.variable_guide_vanes==True:
            self.angle=engine.arguments[self.name_of_angle]
        self.A_G_ncorr_value=self.A_G_ncorr.calculate()
        self.A_G_Re_value=self.A_G_Re.calculate()
        self.A_PR_ncorr_value=self.A_PR_ncorr.calculate()
        self.A_PR_Re_value=self.A_PR_Re.calculate()
        self.A_Eff_ncorr_value=self.A_Eff_ncorr.calculate()
        self.A_Eff_Re_value=self.A_Eff_Re.calculate()
        
        #TODO!!! Временный костыль!!! убоать! 
        if engine.name_of_engine=='GTE-170':
            self.G_corr_map_calc=float(self.G_map(self.n_corr/self.ident_n_value,self.betta,self.angle))*self.A_G_ncorr_value*self.A_G_Re_value*self.ident_G_value
        else:
            self.G_corr_map_calc=float(self.G_map(self.n_corr/self.ident_n_value,self.betta))*self.A_G_ncorr_value*self.A_G_Re_value*self.ident_G_value
        self.G_corr_error=(self.G_corr_map_calc-self.inlet.G_corr)/self.inlet.G_corr #считаем невязку
        
        #TODO!!! Временный костыль!!! убоать! 
        if engine.name_of_engine=='GTE-170':
            self.PRtt=(float(self.PR_map(self.n_corr/self.ident_n_value,self.betta,self.angle))-1.0)*self.A_PR_ncorr_value*self.A_PR_Re_value*self.ident_PR_value+1.0#из характеристики ищем PR
            self.Efftt=float(self.Eff_map(self.n_corr/self.ident_n_value,self.betta,self.angle))*self.A_Eff_ncorr_value*self.A_Eff_Re_value*self.ident_Eff_value#из характеристики ищем кпд
        else:
            #TODO!!! Важно помнить, что в данной модели для Климова не корректно домножается величина PR из характеристики на поправочный коэффициент (напрямую), корректно сначала вычесть 1, домножить на коэффициент, потом прибавить 1. Для любой не климовской модели нужно исправить на корректный варинат
            # self.PRtt=float(self.PR_map(self.n_corr/self.ident_n_value,self.betta))*self.A_PR_ncorr_value*self.A_PR_Re_value*self.ident_PR_value#из характеристики ищем PR
            #это корркетный вариант расчета поправки к PR (см.TODO чуть выше)  
            self.PRtt=(float(self.PR_map(self.n_corr/self.ident_n_value,self.betta))-1.0)*self.A_PR_ncorr_value*self.A_PR_Re_value*self.ident_PR_value+1.0#из характеристики ищем PR
            self.Efftt=float(self.Eff_map(self.n_corr/self.ident_n_value,self.betta))*self.A_Eff_ncorr_value*self.A_Eff_Re_value*self.ident_Eff_value#из характеристики ищем кпд
#        self.inlet.calculate() #еще раз уточняем сечение на входе, т.к. там появилось значение расхода воздуха
        self.outlet.mass_comp=self.inlet.mass_comp
        self.outlet.R = td.R_mix(self.outlet.mass_comp)
        # self.outlet.calculate_R()
        self.outlet.P=self.inlet.P*self.PRtt
        T_outlet_isentropic=td.T2_thru_P1T1P2(self.inlet.P,self.inlet.T,self.outlet.P,self.outlet.mass_comp,self.outlet.R,self.inlet.T-dT,2500)
        L_isentropic=td.H(T_outlet_isentropic,self.outlet.mass_comp)-self.inlet.H
        self.L=L_isentropic/self.Efftt
        self.outlet.H=self.inlet.H+self.L
        self.outlet.T=td.T_thru_H(self.outlet.H,self.outlet.mass_comp,T_outlet_isentropic,2500)
        #рассчитываем отборы и вдувы воздуха
#        (air_bleed_out,air_bleed_in,G0,N0,Gmid,Nmid,G1,N1)= secondary_air_system(self,self.Efftt,self.inlet.G,air_bleed_out,air_bleed_in)
#        secondary_air_system.update_Gref() #обновляем значение ссылочного расхода воздуха
        G0,N0,Gmid,Nmid,G1,N1=engine.secondary_air_system.calculate_bleedout_compressor(self,engine.arguments['Gref'])
        #в случае если происходит подвод воздуха, то нужно учесть изменение его состава чуть выше в строках где считаются mass_comp и R в сечении outlet
        self.outlet.G=self.inlet.G+(G0+Gmid+G1)
        self.outlet.calculate_thru_FG()
        self.N=-self.outlet.G*self.L+(N0+Nmid+N1)
        self.PRts=self.outlet.Ps/self.inlet.P
        
        engine.residuals[self.name_of_G_error]=self.G_corr_error #фигачим в словарь невязку по приведенному расходу
        engine.balance_of_power_of_rotor[self.name_of_n]+=self.N #добавляем величину поребляемой компрессором мощности в невязку по мощности для данного ротора
        # if self.variable_guide_vanes==True: 


#        Ls=self.outlet.Hs-self.inlet.H
#        self.Effts=L_isentropic/Ls #!!!вспомнить как считается кпд по статическим параметрам
#        self.dKy #TODO!!!реализовать расчет ГДУ
        
    def status(self):
        print('ПАРАМЕТРЫ КОМПРЕССОРА:')
        for att in dir(self):
            if att[0]!='_' and att!='status' and att!='calculate':
                print (att,' = ', getattr(self,att))
        print('ПАРАМЕТРЫ НА ВХОДЕ В КОМПРЕССОР:')        
        self.inlet.status()
        print('ПАРАМЕТРЫ НА ВЫХОДЕ ИЗ КОМПРЕССОРА:')        
        self.outlet.status()
        
class Turbine():
    def __init__(self, initial_data, upstream, engine ,name):
        self.name=name
#        id_names.append(name)
#        id_links.append(self)
        engine.devices[name] = self
        self.rotor=int(initial_data[name+'.rotor']) #номер ротора (этот номер должен быть согласован с другими узлами ГТД на этом же роторе, т.е. узлы (турбина) на одном роторе имеют один номер ротора)
        self.name_of_n='n'+str(self.rotor)
        self.name_of_betta=name+'_betta'
        self.name_of_error=name+'_capacity'
        self.name_of_N_error=self.name_of_n+'_dN'
        engine.arguments[self.name_of_n]=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий обороты 
        engine.arguments[self.name_of_betta]=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий вспомогательную переменную бетта для расчета характеристики

#        self.id=len(id_names)-1
        self.upstream=upstream
        self.inlet=upstream.outlet
        self.throttle=td.CrossSection(self.name) #примем что это сечение соответствует горлу первого (если их больше) соплового аппарата в турбине
        self.outlet=td.CrossSection(self.name)
        self.n_phys=np.nan #физические обороты ротора
        self.n_corr=np.nan#приведенные обороты ротора
        self.PRtt=np.nan#степень повышения полного давления
        self.PRts=np.nan#степень повышения статического давления на выходе
        self.L=np.nan#удельная работа TODO! эту штуку сложно посчитать, если учитывать подводы охлаждающего воздуха, поэтому пока что она в результаты не выводится - надо бы допилить
        self.sigmaNGV=1#потери полного давления в сопловом аппарате !!!(в данной модели исходим из того, что сигма = 1, иначе нужно подумать как быть с пропускной способностью - смотри пояснения к Cap_map ниже)
        self.Efftt=np.nan#кпд
        self.Effts=np.nan#кпд по статическим параметрам на выходе
        _Eff_mech=initial_data.get(name+'.Eff_mech',None)
        if _Eff_mech is None:
            self.Eff_mech=default_function(1.0)
        elif isinstance(_Eff_mech,str):
            self.Eff_mech = default_function(float(_Eff_mech))
        else:
            self.Eff_mech=initial_data.get((name+'.Eff_mech'))#механический кпд
        self.Eff_mech_value=np.nan
        self.N=np.nan#мощность турбины, отсюда уже вычтены потери от механического кпд и отборы мощности
        self.Alfa_outlet=np.nan
        self.Lambda_outlet=np.nan
        self.betta=np.nan#вспомогательная переменная, характеризующая положение расчетной точки на характеристике. Ее нормальное значение от 0 до 1, допускаются небольшие отклонения, которые говорят о том, что расчет идет в области экстраполяции, т.е. с низкой точностью
        self.Re=np.nan 
        
        self.A_Cap_Re=initial_data.get((name+'.A_Cap_Re'),default_function(1))
        self.A_Cap_Re.check_parameters(self)
        self.A_PR_Re=initial_data.get((name+'.A_PR_Re'),default_function(1))
        self.A_PR_Re.check_parameters(self)        
        self.A_Eff_Re=initial_data.get((name+'.A_Eff_Re'),default_function(1))
        self.A_Eff_Re.check_parameters(self)          
        self.A_A_Re=initial_data.get((name+'.A_Alfa_Re'),default_function(1))
        self.A_A_Re.check_parameters(self)        
        self.A_L_Re=initial_data.get((name+'.A_lambda_Re'),default_function(1))
        self.A_L_Re.check_parameters(self)      
        
        self.A_Eff_PR=initial_data.get((name+'.A_Eff_PR'),default_function(1))
        self.A_Eff_PR.check_parameters(self)  
        
        self.A_Cap_Re_value=np.nan #коэффициенты А - искусственные поправочные коэффициенты к характеристикам
        self.A_PR_Re_value=np.nan
        self.A_Eff_Re_value=np.nan
        self.A_A_Re_value=np.nan
        self.A_L_Re_value=np.nan     
        
        self.A_Eff_PR_value=np.nan
        
        #для увязки
        self.ident_Cap_value=initial_data.get('ident.'+name+'.Cap',1.0)
        self.ident_PR_value=initial_data.get('ident.'+name+'.PR',1.0)
        self.ident_Eff_value=initial_data.get('ident.'+name+'.Eff',1.0)
        self.ident_n_value=initial_data.get('ident.'+name+'.n',1.0)
        self.ident_A_value=initial_data.get('ident.'+name+'.A',1.0)
        self.ident_L_value=initial_data.get('ident.'+name+'.L',1.0)
        self.ident_Eff_mech_value=initial_data.get('ident.'+name+'.Eff_mech',1.0)

        self.T_throttle_design_point=initial_data[name+'.T_inlet_dp']#температура в горле в расчетной точке (т.е. на режиме, на котором проводилось проектирование турбины)
        self.P_inlet_design_point=initial_data[name+'.P_inlet_dp']#давление на входе в расчетной точке (т.е. на режиме, на котором проводилось проектирование турбины)
        self.Cap_map=initial_data[name+'.Capacity_map'] #!!!есть одна особенность с вычислением пропускной способности. Для экспериментальных характеристик обычно используют давление перед турбиной, а температуру и расход в горле. Это надо помнить и понимать и при необходимости корректировать модель. В данном случае будем подразумевать, что нужная нам пропускная способность - в горле
        self.PR_map=initial_data[name+'.PR_map']
        self.Eff_map=initial_data[name+'.Eff_map']
        self.A_map=initial_data[name+'.A_map']
        self.L_map=initial_data[name+'.L_map']
        self.N_offtake=initial_data.get((name+'.N_offtake'),0.0) #TODO! вообще лучше использовать самописный аналог функции get, потому что get не может возвращать функцию, а в initial_data иногда может задаваться функция для различных параметров. В данный момент в этой роли работает функция extract
        self.Cap_error=np.nan
        self.Cap_map_calc=np.nan
        _F=initial_data.get((name+'.F_inlet'),np.nan)
        if ~np.isnan(self.inlet.F) and ~np.isnan(_F):
            print('В узлах %s и %s конфликт площадей: %.3f и %.3f' % (self.name,self.upstream.name,_F,self.inlet.F))
            raise SystemExit
        elif np.isnan(self.inlet.F) and ~np.isnan(_F):
            self.inlet.F=_F

        self.throttle.F=initial_data.get((name+'.F_throttle'),np.nan)
        self.outlet.F=initial_data.get((name+'.F_outlet'),np.nan)
        initial_data['amount_of_rotors'].add(self.rotor)
        initial_data['amount_of_betta']+=1
        self.betta_id=initial_data['amount_of_betta']
        
        self.Re_dp=(1.019716e-005*initial_data[name+'.P_inlet_dp'])/td.Dyn_visc_klimov(initial_data[name+'.T_inlet_dp'])/(np.sqrt(initial_data[name+'.T_inlet_dp'])) #TODO!!! проверить
        
#        self.G_inlet_corr_map=np.nan #попробуем не использовать невязку по приведенному расходу между расчетной венличиной и характеристикой
    def calculate(self,engine):
        #!!!ввести проверку на наличие необходимого минимума данных для начала расчета
#        self.inlet.calculate() #по возможности уточняем уже известные параметры если для этого достаточно данных
        self.throttle.P=self.inlet.P*self.sigmaNGV 
        
        #для расчета параметров в горле от расчета вторички на данном этапе нужно знать параметры воздуха подводимого до горла СА (P, T, Mass_comp, H, R, G)
#        secondary_air_system.update_Gref() #обновляем значение ссылочного расхода воздуха
        h0, G0, mass_comp_bld0, R_bld = engine.secondary_air_system.calculate_bleedin_before_turbine_throttle(self,engine.arguments['Gref'])
        
        self.throttle.G=self.inlet.G+G0
        self.throttle.H=(self.inlet.H*self.inlet.G+h0*G0)/self.throttle.G
        self.throttle.mass_comp=(self.inlet.mass_comp*self.inlet.G+mass_comp_bld0*G0)/self.throttle.G
        self.throttle.calculate_thru_FG()
        
        #в формуле ниже для вычисления числа рейнольдса давление должно задаваться в кгс/см2 TODO! нужно сделать возможность пользователю задавать формулу для вычисления числа Рейнотльдса и в компрессоре и в турбине через исходные данные
        self.Re=((1.019716e-005*self.throttle.P)/td.Dyn_visc_klimov(self.throttle.T)/(np.sqrt(self.throttle.T)))/self.Re_dp
        #далее поправочные коэффициенты
        self.A_Cap_Re_value=self.A_Cap_Re.calculate()
        self.A_PR_Re_value=self.A_PR_Re.calculate()
        self.A_Eff_Re_value=self.A_Eff_Re.calculate()
        self.A_A_Re_value=self.A_A_Re.calculate()
        self.A_L_Re_value=self.A_L_Re.calculate()
        
        self.n_phys=engine.arguments[self.name_of_n]#массив variables будет построен по следующей схеме {0)Th,1)Ph,2)Humidity, 3)Mach number,4)Ginlet,5)Gfuel,6)n1,...,nx, x)betta...}
        self.n_corr=self.n_phys*np.sqrt(self.T_throttle_design_point/self.throttle.T)#для расчета характеристик вычисляем приведенные обороты на основе заданных физических
#        _func=lambda _betta: self.throttle.capacity-self.A_Capacity_corr*float(self.Cap_map(n_corr_corrected,_betta))
#        self.betta=brentq(_func,-0.5,1.5,disp=True)
        self.betta=engine.arguments[self.name_of_betta]
        self.Cap_map_calc=self.A_Cap_Re_value*self.ident_Cap_value*(float(self.Cap_map(self.n_corr/self.ident_n_value,self.betta)))
        self.Cap_error=(self.Cap_map_calc-self.throttle.capacity)/self.throttle.capacity #!!!!!!важно помнить, что почти всегда пропускная способность считается по полному давлению перед турбиной, а не как здеси и как правильно, т.е. по давлению в горле. Поэтому если вдург в СА будут задаваться полные потери давления, то это нужно учесть и подумать, как поменять алгоритм расчета
        #TODO!!! Важно помнить, что в данной модели для Климова не корректно домножается величина PR из характеристики на поправочный коэффициент (напрямую), корректно сначала вычесть 1, домножить на коэффициент, потом прибавить 1. Для любой не климовской модели нужно исправить на корректный варинат
        self.PRtt=self.A_PR_Re_value*self.ident_PR_value*(float(self.PR_map(self.n_corr/self.ident_n_value,self.betta)))#из характеристики ищем PR
#это корркетный вариант расчета поправки к PR (см.TODO чуть выше)  self.PRtt=self.A_PR_Re_value*(float(self.PR_map(self.n_corr,self.betta))-1.0)+1.0#из характеристики ищем PR
        self.A_Eff_PR_value=self.A_Eff_PR.calculate()
        self.Efftt=self.A_Eff_Re_value*self.A_Eff_PR_value*self.ident_Eff_value*float(self.Eff_map(self.n_corr/self.ident_n_value,self.betta))#из характеристики ищем кпд
        self.Alfa_outlet=self.A_A_Re_value*self.ident_A_value*float(self.A_map(self.n_corr/self.ident_n_value,self.betta))
        self.Lambda_outlet=self.A_L_Re_value*self.ident_L_value*float(self.L_map(self.n_corr/self.ident_n_value,self.betta))
        self.outlet.P=self.inlet.P/self.PRtt
        
        #здесь д.б. учет подвода воздуха в середине и  в конце турбины, должны быть известны: G, H, mass_comp и R, также мощность вырабатываемая подводимым воздухом
        Hmid, Gmid, H1, G1, mass_comp_bld, R_bld, Nbld = engine.secondary_air_system.calculate_bleedin_after_turbine_throttle(self,engine.arguments['Gref'])
        
        self.outlet.G=self.throttle.G+Gmid+G1
        self.outlet.mass_comp=(self.throttle.mass_comp*self.throttle.G+mass_comp_bld*(Gmid+G1))/self.outlet.G  
        
        T_outlet_isentropic_before_mix_with_bld=td.T2_thru_P1T1P2(self.throttle.P,self.throttle.T,self.outlet.P,self.throttle.mass_comp,self.throttle.R,200,self.throttle.T+dT)
        L_isentropic_before_mix_with_bld=self.throttle.H-td.H(T_outlet_isentropic_before_mix_with_bld,self.throttle.mass_comp)
        L_real_before_mix_with_bld=L_isentropic_before_mix_with_bld*self.Efftt
        _H_turbine_outlet_before_mix_with_bld=self.throttle.H-L_real_before_mix_with_bld
        self.outlet.H=(_H_turbine_outlet_before_mix_with_bld*self.throttle.G+Hmid*Gmid+H1*G1)/self.outlet.G
        
#        self.outlet.T=td.T_thru_H(self.outlet.H,self.outlet.mass_comp,T_outlet_isentropic,2500)
        self.outlet.calculate_thru_FG()
        self.Eff_mech_value=self.Eff_mech.calculate()*self.ident_Eff_mech_value
        self.N=(self.throttle.G*L_real_before_mix_with_bld+Nbld)*self.Eff_mech_value+self.N_offtake #TODO! на момент написания этой строки мне непоянтно, нужно ли вынести за скобку отбираемую мощность N_offtake - надо подумать. Неочевидно, но вроде бы турбина выработала какую-то мощность, потеряла часть энергии в виде механического кпд (потери в подшипниках и т.п.), а после этого от нее отобрали мощность на агрегаты
        self.PRts=self.inlet.P/self.outlet.Ps
        
        engine.residuals[self.name_of_error]=self.Cap_error #фигачим в словарь невязку по пропускной способности
        engine.balance_of_power_of_rotor[self.name_of_n]+=self.N #добавляем величину поребляемой компрессором мощности в невязку по мощности для данного ротора


#        Ls=self.outlet.Hs-self.inlet.H
#        self.Effts=L_isentropic/Ls #!!!вспомнить как считается кпд по статическим параметрам
    def status(self):
        print('ПАРАМЕТРЫ ТУРБИНЫ:')
        for att in dir(self):
            if att[0]!='_' and att!='status' and att!='calculate':
                print (att,' = ', getattr(self,att))
        print('ПАРАМЕТРЫ НА ВХОДЕ В ТУРБИНУ:')        
        self.inlet.status()
        print('ПАРАМЕТРЫ В ГОРЛЕ СА ТУРБИНЫ:')        
        self.throttle.status()
        print('ПАРАМЕТРЫ НА ВЫХОДЕ ИЗ ТУРБИНЫ:')        
        self.outlet.status()
        

#считаем полное тепловыделение (не удельное!, т.е. не на 1 кг топлива)
def Hu(T_fuel,T_air,T_gas,G_fuel,G_air,mass_comp_air,mass_comp_fuel,mass_comp_gas):
    return td.H(T_gas,mass_comp_gas)*(G_fuel+G_air)-(td.H(T_fuel,mass_comp_fuel)*G_fuel+td.H(T_air,mass_comp_air)*G_air)

#далее функция, рассчитывающая свойства продуктов сгорания топлива и воздуха. Ее нужно каждый раз корректировать при созданииновой модели двигателя
#т.е. нужно точно знать какое топливо применяется, его теплофизические/термодинамические свойства, молярная масса, условный состав (или взамен стехиометрическую постоянную и газовую постоянную и т.п) и на основе этих данных корректировать алгоритм
#состав рабочего тела задаем в формате mass_comp(N2,O2,Ar,CO2,H2O,керосин_газ,керосин_жидкий)


   
#свойства воздуха и топлива
# dry_air_test=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00,0.0000e+00])
# fuel_test=np.array([0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 1.0000e+00])

#ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КАМЕРЫ СГОРНАИЯ
#теплонапряженность в КС
def Gamma(G, P, T, Volume): #вспомогательная функция из книги Gas Turbine Performance - Fletcher, она рассчитывает тепловую нагрузку в КС
    return G/((P*1E-5)**1.8*np.exp(T/300)*Volume) #оригинальная формула написана для баров, кельвин, кубометров и кг/с, соответственно коэффициенты подобраны под эти единицы
#полнота сгорания топлива в КС
def Efficiency_combustor(Gamma,Gamma_dp,Eff_dp): #формула из книги fletcher "gas turbine performance", плохо согласуется с данными Нк-38СТ, возможно стоит заменить чем-то
    y=np.log10(1-Eff_dp)+1.6*np.log(Gamma/Gamma_dp) #коэффициент 1.6 может меняться для лучшего соответствия экспериментальным данным
    return 1-10**y

class Combustor():
    def __init__(self, initial_data, upstream, engine, name):
        self.name=name
#        id_names.append(name)
#        id_links.append(self)
        engine.devices[name] = self
        self.name_of_Gf=name+'_Gf'
        engine.arguments[self.name_of_Gf]=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий расход топлива
#        self.id=len(id_names)-1
        self.upstream=upstream
        self.inlet=upstream.outlet
        self.outlet=td.CrossSection(self.name)
        self.alfa=np.nan #альфа рассчитываемая автоматом
        self.alfa_manual=np.nan #альфа задаваемая вручную (в модели Климова задаем вручную)

        #в узлах типа "камера сгорания" должна задаваться функция потерь полного давления через раздел {Functions} в исходных данных
        self.sigma_map=initial_data.get((name+'.sigma'),np.nan)
        if self.sigma_map is np.nan:
            print('В исходных данных для узла '+self.name+' не задана характеристика потерь давления sigma')
            raise SystemExit
        # self.sigma_map.check_parameters(self)

        # в узлах типа "камера сгорания" должна задаваться функция полнота сгорания через раздел {Functions} в исходных данных
        self.eff_map=initial_data.get(name+'.eff',np.nan)
        if self.eff_map is np.nan:
            print('В исходных данных для узла '+self.name+' не задана характеристика полноты сгорания eff')
            raise SystemExit  #TODO! обнаружился такой баг: при вызове self.Eff_map.calculate() функция пытается найти аргумент, необходимый ей для расчета alfa_manual, но на данном этапе  он неизвестен, отсюда приложение крашится
        # self.Eff_map.check_parameters(self)
        
        #для увязки
        self.ident_sigma_value=initial_data.get('ident.'+name+'.sigma',1.0)
        self.ident_Eff_value=initial_data.get('ident.'+name+'.eff',1.0)

        self.sigma = np.nan
        self.N_real=np.nan#тепловой поток от сгорания топлива
        self.N_ideal=np.nan#максимально возможный тепловой поток от сгорания топлива при его полном сгорании
        self.Ginlet_dp=initial_data.get(name+'.G_inlet_dp',np.nan)
        self.Pinlet_dp=initial_data.get(name+'.P_inlet_dp',np.nan)
        self.Tinlet_dp=initial_data.get(name+'.T_inlet_dp',np.nan)
        self.Eff_dp=initial_data.get(name+'.Eff_dp',np.nan)
        self.Volume=initial_data.get(name+'.Volume',np.nan) #объем жаровой трубы
        self.Gamma=np.nan #параметр из Gas Turbine Performance - Fletcher, вроед бы это что-то типа теплонапряженности КС
        self.Gamma_dp=Gamma(self.Ginlet_dp,self.Pinlet_dp,self.Tinlet_dp,self.Volume)
        
        #TODO!!! сделать штуку, которая бы переключала возможность вычисления полноты сгорания по методике gas turbine performance и выводила эту инфу в лог
        self.Th=np.nan
        self.Gair_in_burner=np.nan #расход воздуха через жаровую трубу, т.е. с вычитом воздуха на отборы из КС
        self.G_fuel=np.nan
        self.T_fuel=initial_data[name+'.T_fuel'] #TODO! сделать так, чтобы температуру топлива можно было задавать как констртанту, как функцию или чтобы по умолчанию она равнялась температуре окружающей среды
        self.H_fuel=np.nan
        self.Hu_real=np.nan
        self.Hu_ideal_298=np.nan
        self.mass_comp_fuel=initial_data['mass_comp_fuel']
        self.L0_manual=initial_data.get((name+'.L0'),np.nan) #TODO! сделать алгоритм с возможностью задавать L0 вручную так, чтобы это влияло на состав продуктов сгорания, сейчас L0 dычисляется исходя из состава топлива CxHy
        self.L0=td.Stoichiometric_const(Cx=1,Hy=4,mass_comp_air=engine.ambient.external_conditions.mass_comp, mass_comp_fuel=self.mass_comp_fuel) if np.isnan(self.L0_manual) else self.L0_manual



        _F=initial_data.get((name+'.F_inlet'),np.nan)
        if ~np.isnan(self.inlet.F) and ~np.isnan(_F):
            print('В узлах %s и %s конфликт площадей: %.3f и %.3f' % (self.name,self.upstream.name,_F,self.inlet.F))
            raise SystemExit
        elif np.isnan(self.inlet.F) and ~np.isnan(_F):
            self.inlet.F=_F
        self.outlet.F=initial_data.get((name+'.F_outlet'),np.nan)


    def calculate(self,engine):
#        должны быть заданы Pinlet, Tinlet, Tfuel, Gfuel, Gair, dp(Ginlet, Pinlet, Tinlet)
        
        self.G_fuel=engine.arguments[self.name_of_Gf]*self.inlet.G/15 #в данном случае в массиве variables задается относительный расход топлива, это сделано для удобства, чтобы каждый раз не корректировать первоначальный приближения. Относительный расход топлива равен приблизительно от 0 до 1, но может и немного отклоняться от этого диапазона. В формуле число 15 - это примерный стехиометрический коэффициент для керосина.
        self.H_fuel=td.H(self.T_fuel,self.mass_comp_fuel)
        self.Gamma=Gamma(self.inlet.G,self.inlet.P,self.inlet.T,self.Volume)
        self.sigma=self.sigma_map.calculate()*self.ident_sigma_value
        #TODO!!! также нужно подумать, как реализовать такую штуку: нужно иметь возможность задавать функцию в зависимости от какого-то параметра, который на данном этапе еще не вычислен, но он может быть известен на предыдущей итерации, соответственно его можно взять из предыдущей итерации. Например, в данном случае это коэффициент потерь полного давления в КС сигма, который должен зщависеть от расхода воздуха на выходе, который на данном этапе еще неизвестен
        self.outlet.P=self.inlet.P*self.sigma
        
        #здесь должен быть расчет отбора, для расчета КС нужны величины: G, 
#        secondary_air_system.update_Gref() #обновляем значение ссылочного расхода воздуха
        G0,Gmid,G1=engine.secondary_air_system.calculate_bleedout_combustor_and_channel(self,engine.arguments['Gref'])
        
        self.Gair_in_burner=self.inlet.G+(G0+Gmid+G1)
        # self.alfa_manual=1/14.947683109118086696562032884903/(self.G_fuel/self.Gair_in_burner) #TODO! должен задавать пользователь через исходные данные #TODO!!! стехиометрическая постоянная для керосина 14,73!!! почти наверняка, нужно проверить у иностранного кероисна
        self.outlet.G=self.Gair_in_burner+self.G_fuel
        self.eff=self.ident_Eff_value*self.eff_map.calculate()   #*Efficiency_combustor(self.Gamma,self.Gamma_dp,self.Eff_dp) - вариант вычисления по методике из gas Turbine Performance

        rez=td.Combustion_properties(self.inlet.mass_comp, self.mass_comp_fuel, self.G_fuel, self.Gair_in_burner,self.H_fuel,self.inlet.H, self.eff)
        self.alfa=rez[1]
        self.outlet.mass_comp=rez[2]
        self.outlet.H=rez[3]
        self.Hu_real=rez[4] #теплотворная способность топлива из функции Combustion_properties рассчитывается с учетом полноты сгорания, поэтому чтобы узнать теоретическую идеальную Hu нужно в эту функцию подставить полноту сгорания = 1
        self.Hu_ideal_298=Combustion_properties(self.inlet.mass_comp, self.mass_comp_fuel, self.G_fuel, self.inlet.G,self.T_fuel,self.inlet.T, 1)[4]
        self.N_real=self.G_fuel*self.Hu_real #реальная тепловая мощность сгорания топлива в кс 
        self.N_ideal=self.G_fuel*self.Hu_ideal_298
        self.outlet.calculate_thru_FG()
    def status(self):
        print('ПАРАМЕТРЫ КАМЕРЫ СГОРАНИЯ:')
        for att in dir(self):
            if att[0]!='_' and att!='status' and att!='calculate':
                print (att,' = ', getattr(self,att))
        print('ПАРАМЕТРЫ НА ВХОДЕ В КАМЕРУ СГОРАНИЯ:')        
        self.inlet.status()
        print('ПАРАМЕТРЫ НА ВЫХОДЕ ИЗ КАМЕРЫ СГОРАНИЯ:')        
        self.outlet.status()
        
class Channel():
    def __init__(self, initial_data, upstream,engine,name):
        self.name=name
#        id_names.append(name)
#        id_links.append(self)
        engine.devices[name] = self
#        self.id=len(id_names)-1
        self.upstream=upstream
        self.inlet=upstream.outlet
        self.outlet_ideal=td.CrossSection(self.name)
        self.outlet=td.CrossSection(self.name)
        _F=initial_data.get((name+'.inlet.F'),np.nan)
        if ~np.isnan(self.inlet.F) and ~np.isnan(_F):
            solverLog.error('В узлах %s и %s конфликт площадей: %.3f и %.3f' % (self.name,self.upstream.name,_F,self.inlet.F))
            raise SystemExit
        elif np.isnan(self.inlet.F) and ~np.isnan(_F):
            self.inlet.F=_F

        self.outlet_ideal.F=initial_data.get((name+'.outlet.F'),np.nan)

        
        #в узлах типа "канал" должна задаваться функция потерь полного давления через раздел {Functions} в исходных данных
        self.sigma=initial_data.get((name+'.sigma'),np.nan)
        self.sigma_corrected=np.nan #тут будем хранить сигму с учетом поправок по увязочному коэффициенту
        
        #для увязки
        self.ident_sigma=initial_data.get('ident.' + name + '.sigma', 1.0)

        self.fi=initial_data.get((name+'_fi'),1.0) #коэффициент скорости, в основном нужен для сопла, для прочих условий принимаем его равным 1
        self.Eff=np.nan
        self.Hs_isentropic_ideal=np.nan
        #TODO!!!NB!!! далее костыль - перепуск воздуха для ТВ7, НЕ ЗАБЫТЬ ИЗБАВИТЬСЯ ОТ НЕГО!
        if engine.name_of_engine=='TV7-117' and self.name=='lpc_hpc_interduct':
            _n_x=np.array([0,0.63,0.73,0.75,0.751])
            _v_y=np.array([0.1,0.1,0.0955,0.093,0.0])
            self.v_perepusk_TV7=interp1d(_n_x,_v_y,bounds_error=False,fill_value=(0.1,0.0))
            self.perepusk=np.nan
        #TODO!!!NB!!! выше костыль - перепуск воздуха для ТВ7

    @property
    def sigma(self):
        return self.sigma_map.calculate()

    @property.setter
    def sigma(self,x):
        self.sigma_map=x
        if self.sigma_map is np.nan:
            solverLog.info('Error! В исходных данных для узла '+self.name+' не задана характеристика потерь давления sigma')
            raise SystemExit

    def calculate(self,engine):
        #определить обязательные параметры
        """
        обязательные параметры:
        Pвх - из ПРЕдыдущего узла
        Tвх - пре
        sigma_map - из исходных данных
        Gвх - задается из массива variables
        """

        self.inlet.calculate_thru_FG() #уточним параметры во входном сечении, т.к. если перед каналом стоит объект Ambient, то известны не все параметры, только P, T, G, mass_comp
        self.sigma_corrected=self.sigma*self.ident_sigma

        self.outlet_ideal.P=self.inlet.P*self.sigma_corrected
               
        #здесь должен быть учет отборов, должны быть извсетны величины отбираемого воздуха
#        secondary_air_system.update_Gref() #обновляем значение ссылочного расхода воздуха
        G0_out,Gmid_out,G1_out=engine.secondary_air_system.calculate_bleedout_combustor_and_channel(self,engine.arguments['Gref'])
        
        #TODO!!!NB!!! далее костыль - перепуск воздуха для ТВ7, НЕ ЗАБЫТЬ ИЗБАВИТЬСЯ ОТ НЕГО!
        if engine.name_of_engine=='TV7-117' and self.name=='lpc_hpc_interduct':
            _n_corr=self.upstream.n_corr
            _G_in_ok=engine.secondary_air_system.section_for_Gref.G
            self.perepusk=self.v_perepusk_TV7(_n_corr)*_G_in_ok
            G0_out-=-self.perepusk
        #TODO!!!NB!!! выше костыль - перепуск воздуха для ТВ7
        
        #и учет вдувов
        G0_in,H0_in,Gmid_in,Hmid_in,G1_in,H1_in,mass_comp_bld_in, R_bld_in=engine.secondary_air_system.calculate_bleedin_channel(self,engine.arguments['Gref'])

        self.outlet_ideal.G=self.inlet.G+(G0_out+Gmid_out+G1_out)+(G0_in+Gmid_in+G1_in)
        self.outlet_ideal.H=(self.inlet.H*self.inlet.G+H0_in*G0_in+Hmid_in*Gmid_in+H1_in*G1_in)/self.outlet_ideal.G
        self.outlet_ideal.mass_comp=(self.inlet.mass_comp*(self.inlet.G+(G0_out+Gmid_out+G1_out))+mass_comp_bld_in*(G0_in+Gmid_in+G1_in))/self.outlet_ideal.G        
        self.outlet_ideal.calculate_thru_FG()
        if self.fi<1:
            self.outlet.P=self.outlet_ideal.P
            self.outlet.H=self.outlet_ideal.H
            self.outlet.G=self.outlet_ideal.G
            if np.isnan(self.outlet.F):
                self.outlet.F=self.outlet_ideal.F
            self.outlet.mass_comp=self.outlet_ideal.mass_comp
            self.outlet.V=self.outlet_ideal.V*self.fi
            self.outlet.calculate_thru_FG()
        else:
            self.outlet.copy_attributes(self.outlet_ideal)
        #для сопла иногда может быть необходимо вычислить его кпд через изоэнтропический перепад
        #!!!нужно уточнить формулу кпд сопла, возможно полные параметры должны использовать на выходном сечении,а не на входном, как сейчас
        # if not(np.isnan(self.inlet.P)) and not(np.isnan(self.inlet.T)) and not(np.isnan(self.outlet_ideal.Ps)):
        #     Ts_isentropic_ideal=td.T2_thru_P1T1P2(self.inlet.P,self.inlet.T,self.outlet_ideal.Ps,self.outlet_ideal.mass_comp,self.outlet_ideal.R,200,self.inlet.T+dT)
        #     self.Hs_isentropic_ideal=td.H(Ts_isentropic_ideal,self.outlet_ideal.mass_comp)
        #     #TODO! кпд по-моему считается неправильно, проверить. Замечено при увязке ТВ7 при использовании
        #     self.Eff=(self.outlet_ideal.H-self.outlet.Hs)/(self.inlet.H-self.Hs_isentropic_ideal) #кпд сопла - это отношение кинетической энергии в выходном сопле к идеальному теоретически возможному перепаду
        
        
    def status(self):
        print('ПАРАМЕТРЫ КАНАЛА:')
        for att in dir(self):
            if att[0]!='_' and att!='status' and att!='calculate':
                print (att,' = ', getattr(self,att))
        print('ПАРАМЕТРЫ НА ВХОДЕ В КАНАЛ:')        
        self.inlet.status()
        print('ПАРАМЕТРЫ НА ВЫХОДЕ ИЗ КАНАЛА:') 
        self.outlet.status()


class ConvergentNozzle(Channel): #сужающееся сопло
    def __init__(self, initial_data, upstream, engine,name):
        super().__init__(initial_data, upstream, engine,name)
        self.flowdensity_error=np.nan
        self.name_of_error=self.name+'_flowdensity'
    def calculate(self,engine):       
        self.inlet.calculate_thru_FG() #уточним параметры во входном сечении, т.к. если перед каналом стоит объект Ambient, то известны не все параметры, только P, T, G, mass_comp
        self.sigma= self.ident_sigma * self.sigma_map.calculate() #!!!здесь должна быть какая-то функция, которая задает каким образом вычисляется потери в канале: либо постоянным числом, либо функцией, либо интерполяцией по точкам
        
        self.outlet_ideal.P=self.inlet.P*self.sigma
               
        #здесь должен быть учет отборов, должны быть извсетны величины отбираемого воздуха
#        secondary_air_system.update_Gref() #обновляем значение ссылочного расхода воздуха
        G0_out,Gmid_out,G1_out=engine.secondary_air_system.calculate_bleedout_combustor_and_channel(self,engine.arguments['Gref'])
        #и учет вдувов
        G0_in,H0_in,Gmid_in,Hmid_in,G1_in,H1_in,mass_comp_bld_in, R_bld_in=engine.secondary_air_system.calculate_bleedin_channel(self,engine.arguments['Gref'])

        self.outlet_ideal.G=self.inlet.G+(G0_out+Gmid_out+G1_out)+(G0_in+Gmid_in+G1_in)
        self.outlet_ideal.H=(self.inlet.H*self.inlet.G+H0_in*G0_in+Hmid_in*Gmid_in+H1_in*G1_in)/self.outlet_ideal.G
        self.outlet_ideal.mass_comp=(self.inlet.mass_comp*(self.inlet.G+(G0_out+Gmid_out+G1_out))+mass_comp_bld_in*(G0_in+Gmid_in+G1_in))/self.outlet_ideal.G        
        #в процессе итерации иногда может оказаться, что полное давление будет меньше задаваемого статического противодавления, в этом случае их нужно искусственно корректировать
        if self.outlet_ideal.P<engine.arguments['Ph']:
            self.outlet_ideal.Ps_back=self.outlet_ideal.P*0.999
        else:
            self.outlet_ideal.Ps_back=engine.arguments['Ph'] 
        self.outlet_ideal.calculate_thru_FGPback()
        if self.fi<1:
            self.outlet.P=self.outlet_ideal.P
            self.outlet.H=self.outlet_ideal.H
            self.outlet.G=self.outlet_ideal.G
            self.outlet.F=self.outlet_ideal.F
            self.outlet.mass_comp=self.outlet_ideal.mass_comp
            self.outlet.V=self.outlet_ideal.V*self.fi
            self.outlet.Ps=self.outlet_ideal.Ps
            self.outlet.calculate_thru_FGPback()
        else:
            self.outlet.copy_attributes(self.outlet_ideal)
            
        self.flowdensity_error=self.outlet.flowdensity_error
        #для сопла иногда может быть необходимо вычислить его кпд через изоэнтропический перепад
        #!!!нужно уточнить формулу кпд сопла, возможно полные параметры должны использовать на выходном сечении,а не на входном, как сейчас
        # if not(np.isnan(self.inlet.P)) and not(np.isnan(self.inlet.T)) and not(np.isnan(self.outlet_ideal.Ps)):
        #     Ts_isentropic_ideal=td.T2_thru_P1T1P2(self.inlet.P,self.inlet.T,self.outlet_ideal.Ps,self.outlet_ideal.mass_comp,self.outlet_ideal.R,200,self.inlet.T+dT)
        #     self.Hs_isentropic_ideal=td.H(Ts_isentropic_ideal,self.outlet_ideal.mass_comp)
        #     #TODO! кпд по-моему считается неправильно, проверить. Замечено при увязке ТВ7 при использовании
        #     self.Eff=(self.outlet_ideal.H-self.outlet.Hs)/(self.inlet.H-self.Hs_isentropic_ideal) #кпд сопла - это отношение кинетической энергии в выходном сопле к идеальному теоретически возможному перепаду

        
        
        
        
        
        
        
        #TODO! есть проблема с вычислением параметров в сопле, если заранее неизвестно докритика там или сверхкритика: если статические параметры вычисляются на основе задаваемого расхода при известной площади, то в случае сверхкритики, статические параметры невычисляемы -> ошибка, для избежания этой ошщибки сейчас в классе crosssection сделан алгоритм, который в случае сверхкритики, считает из условия М=1
        #если задается статическиое давление на выходе + площадь сечения, то другая опасность: возможны ситуации, когда статическое давление будет больше полного, величина котрого приходит из расчеты вышестоящего узла, отсюда опять ошибка
        # нужно разобраться с взаимосвязью в процессе расчета площади сечения, расхода и статических параметров. 
        # self.sigma=self.ident_sigma_value*self.sigma_map.calculate() #!!!здесь должна быть какая-то функция, которая задает каким образом вычисляется потери в канале: либо постоянным числом, либо функцией, либо интерполяцией по точкам
        # self.outlet_ideal.P=self.inlet.P*self.sigma
        # if self.outlet_ideal.P>engine.arguments['Ph']:
        #     self.outlet_ideal.Ps=engine.arguments['Ph']
        # super().calculate(engine)
        # if self.outlet.M>=1:
        #     self.outlet_ideal.copy_attributes(self._outlet_ideal)
        #     self.outlet_ideal.M=1
        #     super().calculate(engine)
  
        # self.Ps_error=(self.outlet.Ps-engine.arguments['Ph'])/engine.arguments['Ph'] #невязка по статическому давлению на срезе актуальна только если на сопле докритический перепад, а если сверхкритический?!
        # Cap_fact=self.outlet.capacity/self.outlet.F
        # Cap_calc, Ps, Ts, M, V=Is_flow_critical(self.outlet.P,self.outlet.T,engine.arguments['Ph'],self.outlet.mass_comp)
        # if self.outlet.M<1:
        #     self.Capacity_error=(self.outlet.flowdensity_thru_G-self.outlet.flowdensity_thru_Ps)/self.outlet.flowdensity_thru_Ps
        #     # print('Ps')
        # else:
        #     self.Capacity_error=(self.outlet.flowdensity_thru_G-self.outlet.flowdensity_cr)/self.outlet.flowdensity_cr
            # print('G')
        # print(self.Capacity_error)
        # engine.residuals[self.name_of_error]=self.Ps_error #фигачим в словарь невязку по статическому давлению на срезе
        engine.residuals[self.name_of_error]=self.flowdensity_error #фигачим в словарь невязку по пропускной способности сопла
    def status(self):
        print('ПАРАМЕТРЫ СУЖАЮЩЕГОСЯ СОПЛА:')
        for att in dir(self):
            if att[0]!='_' and att!='status' and att!='calculate':
                print (att,' = ', getattr(self,att))
        print('ПАРАМЕТРЫ НА ВХОДЕ В СУЖАЮЩЕЕСЯ СОПЛО:')        
        self.inlet.status()
        print('ПАРАМЕТРЫ НА ВЫХОДЕ ИЗ СУЖАЮЩЕГОСЯ СОПЛА:')    
        self.outlet.status()
    
            
#класс для описания внешних условий
class Ambient():
    def __init__(self,initial_data,engine):
#        id_names.append('ambient')
#        id_links.append(self)
        self.name='ambient'
        engine.devices['ambient'] = self
        engine.arguments['Th']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий
        engine.arguments['Ph']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий 
        engine.arguments['Hum']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий 
        engine.arguments['M']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий 
        engine.arguments['V']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий. NB!!! нужно потом при заполнении arguments выкинуть или M или V, в зависимости от того, какой параметр задан в исходных данных и какой отсутствует
        engine.arguments['Gin']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий 

#        self.id=len(id_names)-1
        self.external_conditions=td.CrossSection(self.name)
        self.outlet=td.CrossSection(self.name)
        self.humidity=np.nan
        self.mass_comp_dry_air=initial_data['mass_comp_ambient']#здесь задаестя состав сухого воздуха, т.е. без учета влажности, если иначе, то нужно менять алгоритм
        self.WAR=np.nan
    def calculate(self,engine): #массив variables будет построен по следующей схеме {0)Th,1)Ph,2)Humidity, 3)Mach number,4)Ginlet,5)Gfuel,6)n1,...,nx, x)betta...}
                            
        self.external_conditions.Ts=engine.arguments['Th']
        self.external_conditions.Ps=engine.arguments['Ph']
        if 'M' in engine.arguments:
            self.external_conditions.M=engine.arguments['M'] #скорость полета, не скоорость потока через сечение!
        elif 'V' in engine.arguments:
            self.external_conditions.V=engine.arguments['V'] #скорость полета, не скоорость потока через сечение!
        self.humidity=engine.arguments['Hum']
        self.WAR=td.WAR(self.humidity,self.external_conditions.Ps,self.external_conditions.Ts,self.mass_comp_dry_air)
        self.external_conditions.mass_comp=td.WAR_to_moist_air(self.WAR,self.mass_comp_dry_air)
        self.external_conditions.calculate_totPar_thru_statParV()

        self.outlet.G=engine.arguments['Gin'] #массив variables будет построен по следующей схеме {0)Th,1)Ph,2)Humidity, 3)Mach number,4)Ginlet,5)Gfuel,6)n1,...,nx, x)betta...}
        self.outlet.P=self.external_conditions.P
        self.outlet.T=self.external_conditions.T
        self.outlet.mass_comp=self.external_conditions.mass_comp
        self.outlet.calculate_thru_FG()
    def status(self):
        print('ПАРАМЕТРЫ ВНЕШНИХ УСЛОВИЙ:')
        for att in dir(self):
            if att[0]!='_' and att!='status' and att!='calculate':
                print (att,' = ', getattr(self,att))
        self.outlet.status()
        
        
#класс для описания вторичной воздушной системы в упрощенном виде, т.е. прямая задача расчета вторичной воздушной системы не решается        
class Secondary_Air_System():
    #TODO!! доделать функции для возможности отбирать воздух от каналов, подводить воздух куда угодно, возможно отбирать воздуах от турбин (а надо?)
    def __init__(self, initial_data, engine,name):
        self.name=name
        self.name_of_error=name+'_Gref'
        engine.devices[name] = self
        engine.arguments['Gref']=np.nan #сообщаем словарю arguments, что нам нужен параметр, характеризующий ссылочный расход воздуха

        self.devices=engine.devices
        self.air_bleed_out=self.bleed_out_str2mtrx(engine.devices,initial_data['air_bleed_out'])#массив хранят в себе исходные и рассчитанные данный отборов
        self.air_bleed_in=self.bleed_in_str2mtrx(engine.devices,initial_data['air_bleed_in'])#массив хранят в себе исходные и рассчитанные данный вдувов
        
        #для увязки. Пока что в качестве увязочных коэффициентов смогут выступать только коэффициенты характеризующие величину отборов (подводы пока не реализованы - не совсем понятно как это сделать)
        self.ident_G={} #в словаре будут храниться увязочные коэффициенты на величину абсолютного расхода, ключ словаря соответствует номеру отбора из массива self.air_bleed_out.количество элементов с списке равно количеству отборов
        for bleed_out_instance in self.air_bleed_out:
            _number_of_bleed=bleed_out_instance['N'][0]
            self.ident_G[_number_of_bleed]=initial_data.get('ident.SAS.G'+str(_number_of_bleed),1.0)
        
        #ищем чему равен ссылочный расход воздуха, относительно которого задаются расходы воздуха
        temp_Gref=initial_data['air_bleed_Greference'].split(',')
#        device_for_Gref=id_links[id_names.index(temp_Gref[0])]
        device_for_Gref=engine.devices[temp_Gref[0]]
        if temp_Gref[1]=='вх' or temp_Gref[1]=='inlet' or temp_Gref[1]=='вход':
            self.section_for_Gref=device_for_Gref.inlet            
        elif temp_Gref[1]=='вых' or temp_Gref[1]=='outlet' or temp_Gref[1]=='выход':
            self.section_for_Gref=device_for_Gref.outlet
        self.Gref_calc=np.nan #расчетное значение ссылочног орасхода
        self.Gref_var=np.nan#значение ссылочног орасхода из варьируемых переменных
        self.Gref_error=np.nan
        if initial_data['air_bleed_expansion']==True: #проверяем как задал пользователь: учитывать расширение воздуха в каналах вторичной воздушной системы от давления отбора до давления подвода или нет.
            self.bleed_expansion=True
        elif initial_data['air_bleed_expansion']==False:
            self.bleed_expansion=False
        else:
            print('В исходных данных не задан параметр air_bleed_expansion=True/False, характеризующий учет или неучет расширения воздуха в каналах вторичной воздушной системы от давления в точке отбора до давления в точке подвода.') # В случае неучета в турбине работа вдува будет завышена.
            raise SystemExit
  
#    ФУНКЦИЯ ДЛЯ РАСЧЕТА ПАРАМЕТРОВ ОТБОРОВ ОТ УЗЛОВ
    def calculate_bleedout_compressor(self,device,Greference): #device - узел в котором считается вторичка, eff - кпд этого узла (если это компрессор или турбина, иначе = 1), G_ref - расход воздуха относительно которого задаются отборы (обычно расход на входе в компрессор), air_bleed_out,air_bleed_in - массивы отборов и вдувов
        #расчет всех отборов
#        self.Gref_var=Greference
        #bleed_out_instance = [0)number_of_bleed_out/1)from/2)P_rel_from/3)h_rel_from/4)T_rel_from/5)G_rel_from/6)G_abs_from/7)A_from/8)F_from/9)G/10)h_from/11)T_from/12)P_from]
        G0,Gmid,G1=0,0,0 #расходы отборов в начале, в середине и в конце узла соответственно
        N0,Nmid,N1=0,0,0 #мощность, затрачиваемая на сжатие отбора в компрессоре или вырабатываемая вдувом в турбине в начале, в середине и в конце узла соответственно
        for bleed_out_instance in self.air_bleed_out:
            if bleed_out_instance['device_from'].item() is device: #ищем в списке отборов имя данного узла, если находим, значит от этого узла производится отбор, проводим с ним расчет
                P1=device.inlet.P
                T1=device.inlet.T
                H1=device.inlet.H
                P2=device.outlet.P
                T2=device.outlet.T
                H2=device.outlet.H
                mass_comp_bld=device.inlet.mass_comp
                R_bld=device.inlet.R
                if type(device).__name__=='Compressor' or type(device).__name__=='Turbine':
                    Efficiency=device.Efftt
                else:
                    Efficiency=1
                
                #точка отбора может быть задана относительным давлением, энтальпией или температурой. Далее извлекаем из массива bleed_out_instance чем задан отбор в данном случае и в зависимости от этого считаем параметры в точке отбора
                if np.isfinite(bleed_out_instance['P_rel_from']): #если задано P_rel_from (!!!пока не точно, но вроде бы если отбор не от компрессора и не от турбины, то лучше его через P_rel_from не задавать!!! - надо подумать и проверить)
                    Pbld=P1+(P2-P1)*bleed_out_instance['P_rel_from'].item()      
                    Tbld_is=td.T2_thru_P1T1P2(P1,T1,Pbld,mass_comp_bld,R_bld,200,2500)
                    hbld_is=td.H(Tbld_is,mass_comp_bld)
                    hbld=H1+(hbld_is-H1)/Efficiency
                    Tbld=td.T_thru_H(hbld,mass_comp_bld,200,2500)
                    bleed_out_instance['h_rel_from']=(hbld-H1)/(H2-H1)
                    bleed_out_instance['T_rel_from']=(Tbld-T1)/(T2-T1)
                elif np.isfinite(bleed_out_instance['h_rel_from']): #если задано h_rel_from
                    hbld=H1+(H2-H1)*bleed_out_instance['h_rel_from'].item()
                    Tbld=td.T_thru_H(hbld,mass_comp_bld,200,2500)
                    hbld_is=(hbld-H1)*Efficiency+H1
                    Tbld_is=td.T_thru_H(hbld_is,mass_comp_bld,200,2500)
                    Pbld=td.P2_thru_P1T1T2(P1,T1,Tbld_is,mass_comp_bld,R_bld)
                    bleed_out_instance['P_rel_from']=(Pbld-P1)/(P2-P1)
                    bleed_out_instance['T_rel_from']=(Tbld-T1)/(T2-T1)
                elif np.isfinite(bleed_out_instance['T_rel_from']): #если задано T_rel_from
                    Tbld=device.inlet.T+(device.outlet.T-device.inlet.T)*bleed_out_instance['T_rel_from'].item()
                    hbld=td.H(Tbld,mass_comp_bld)
                    hbld_is=(hbld-H1)*Efficiency+H1
                    Tbld_is=td.T_thru_H(hbld_is,mass_comp_bld,200,2500)
                    Pbld=td.P2_thru_P1T1T2(P1,T1,Tbld_is,mass_comp_bld,R_bld)
                    bleed_out_instance['P_rel_from']=(Pbld-P1)/(P2-P1)
                    bleed_out_instance['h_rel_from']=(hbld-H1)/(H2-H1)
                else:
                    print('Неверно задана точка отбора №'+str(bleed_out_instance['N']))
                    raise SystemExit
                #проверяем чем задана величина отбора, она может быть задана относительным расходом G_rel_from, абсолютным G_abs_from, площадью F_from или пропускной способностью A_from
                if np.isfinite(bleed_out_instance['G_rel_from']):#если задано G_rel_from
                    Gbld=Greference*bleed_out_instance['G_rel_from'].item()*self.ident_G[bleed_out_instance['N'][0]] #крайний множитель - это увязочный коэффициент
                    bleed_out_instance['G_abs_from']=Gbld
                elif np.isfinite(bleed_out_instance['G_abs_from']):#если задано G_abs_from
                    Gbld=bleed_out_instance['G_abs_from'].item()*self.ident_G[bleed_out_instance['N'][0]] #крайний множитель - это увязочный коэффициент
                    bleed_out_instance['G_rel_from']=Gbld/Greference
                elif np.isfinite(bleed_out_instance['A_from']):#если задано A_from
                    print('Неверно задана величина отбора №'+str(bleed_out_instance['N'])+ '. Причина: пока что не реализован алгоритм задания величины отбора пропускной способностью G*T^0.5/P')
                    raise SystemExit
                elif np.isfinite(bleed_out_instance['F_from']):#если задано F_from
                    print('Неверно задана величина отбора №'+str(bleed_out_instance['N'])+ '. Причина: пока что не реализован алгоритм задания величины отбора площадью F')
                    raise SystemExit
                else:
                    print('Неверно задана величина отбора №'+str(bleed_out_instance['N']))
                    raise SystemExit
                bleed_out_instance['G_from']=Gbld
                bleed_out_instance['h_from']=hbld
                bleed_out_instance['T_from']=Tbld
                bleed_out_instance['P_from']=Pbld
                bleed_out_instance['mass_comp']=mass_comp_bld
                if bleed_out_instance['h_rel_from']==0: #если отбор в начале узла
                    G0+=-Gbld #знак минус, потому что это отбор от общего расхода через узел
                    N0+=-Gbld*(hbld-H1) #здесь знак минус, потому что эта мощность отбирается от компрессора для сжатия той части  воздуха, которая отбираестя
                elif bleed_out_instance['h_rel_from']==1:  #если отбор в конце узла
                    G1+=-Gbld
                    N1+=-Gbld*(hbld-H1)
                elif bleed_out_instance['h_rel_from']>0 and bleed_out_instance['h_rel_from']<1:  #если отбор в середине узла
                    Gmid+=-Gbld
                    Nmid+=-Gbld*(hbld-H1)

        return G0,N0,Gmid,Nmid,G1,N1
#    ФУНКЦИЯ ДЛЯ РАСЧЕТА ПАРАМЕТРОВ ВДУВОВ В УЗЛЫ ДО ГОРЛА
    def calculate_bleedin_before_turbine_throttle(self,device,Greference): #device - узел в котором считается вторичк
#        self.Gref_var=Greference
        #нужно рассчитать параметры воздуха вдуваемого до горла СА: P, T, Mass_comp, H, R, G
        G0=0 #суммарный расход вдувов
        H0=0 #суммарная энтальпия вдувов
        mass_comp_bld=np.zeros(self.air_bleed_out[0]['mass_comp'][0].shape)#инициализация пустого значения, чтобы питон не ругался - надо будет переделать по человечески
        R_bld=0
        #bleed_out_instance = [0)number_of_bleed_out/1)from/2)P_rel_from/3)h_rel_from/4)T_rel_from/5)G_rel_from/6)G_abs_from/7)A_from/8)F_from/9)G/10)h_from/11)T_from/12)P_from]
        #bleed_in_instance = [0)number_of_bleed_out/1)to/2)P_rel_to/3)h_rel_to/4)T_rel_to5)G_rel_to/6)G_abs_to/7)A_to/8)F_to/9)G/10)h_to/11)T_to/12)P_to]               
        for bleed_in_instance in self.air_bleed_in:
            if bleed_in_instance['device_to'].item() is device: #ищем в списке вдувов имя данного узла, если находим, значит в этот узел производится вдув, проводим с ним расчет
                if bleed_in_instance['P_rel_to']==0: #если вдув производится до горла (считается только для турбины)
                    _row_index=bleed_in_instance['N'].item()-1
#                    name_of_device=self.id_names[bleed_in_instance['device_to'].item()]                    
                    name_of_device=bleed_in_instance['device_to'].item().name                    
#                    P1=device.inlet.P #параметры в начале узла, куда производится вдув
#                    T1=device.inlet.T
#                    H1=device.inlet.H
                    P2=device.throttle.P #параметры в горле турбины, куда производится вдув
                    
                    Pbld_0=self.air_bleed_out[_row_index]['P_from'].item() #bld_0 - параметры в точке отбора
                    Tbld_0=self.air_bleed_out[_row_index]['T_from'].item()
                    Hbld_0=self.air_bleed_out[_row_index]['h_from'].item()
                    Gbld_0=self.air_bleed_out[_row_index]['G_from'].item()                    
                    mass_comp_bld=self.air_bleed_out[_row_index]['mass_comp'][0]
                    R_bld=td.R_mix(mass_comp_bld)
                    Pbld=P2#считаем, что точке подвода равно давлению в горле (хотя на самом деле статическое давление в точке вдува равно статическому давлению в проточной части, но это довольно проблематично учесть в термодинамической модели, а если сюда еще и прибавить возможность существования критического перепада, то все становится еще сложней)
                    if Pbld>Pbld_0:
                        solverLog.info('Давление в точке вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' больше, чем давление в точке отбора. Давление в точке вдува='+str(Pbld)+', давление в точке отбора='+str(Pbld_0))
                        solverLog.info('Искусственно задаем давление в точке вдува равным давлению в точке отбора. Если это сообщение появляется в финальной итерации, то возможна ошибка в расчете отбора.')
                        Pbld=Pbld_0
                        # raise SystemExit
                    #считаем, что в канале вторичной воздушной системы воздух изоэнтропически расширяется от начального давления в точке отбора Pbld_0 до давления в точке подвода Pbld
                    if self.bleed_expansion==True:
                        Tbld=td.T2_thru_P1T1P2(Pbld_0,Tbld_0,Pbld,mass_comp_bld,R_bld,200,Tbld_0+dT)
                        hbld=td.H(Tbld,mass_comp_bld)
                    else:
                        Tbld=Tbld_0
                        hbld=Hbld_0
                    #проверяем чем задана величина вдува, она может быть задана относительным расходом G_rel_to от величины отбора, абсолютным G_abs_to, площадью F_to или пропускной способностью A_to
                    if np.isfinite(bleed_in_instance['G_rel_to']):#если задано G_rel_to
                        Gbld=Gbld_0*bleed_in_instance['G_rel_to'].item()
                        bleed_in_instance['G_abs_to']=Gbld
                    elif np.isfinite(bleed_in_instance['G_abs_to']):#если задано G_abs_to
                        Gbld=bleed_in_instance['G_abs_to'].item()
                        bleed_in_instance['G_rel_to']=Gbld/Gbld_0
                        if bleed_in_instance['G_rel_to']>1:
                            print('Расход воздуха через вдув в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' больше, чем расход отбора, чего не может быть! Отбор='+str(Gbld_0)+', вдув='+str(Gbld))
                    elif np.isfinite(bleed_in_instance['A_to']):#если задано A_to
                        print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+'. Причина: пока что не реализован алгоритм задания величины отбора пропускной способностью G*T^0.5/P')
                        raise SystemExit
                    elif np.isfinite(bleed_in_instance['F_to']):#если задано F_to
                        print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+'. Причина: пока что не реализован алгоритм задания величины отбора площадью F')
                        raise SystemExit
                    else:
                        print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N']))
                        raise SystemExit
                    bleed_in_instance['P_rel_to']=0
                    bleed_in_instance['h_rel_to']=0
                    bleed_in_instance['T_rel_to']=0
                    bleed_in_instance['G_to']=Gbld
                    bleed_in_instance['h_to']=hbld
                    bleed_in_instance['T_to']=Tbld
                    bleed_in_instance['P_to']=Pbld
                    bleed_in_instance['mass_comp']=mass_comp_bld
                    #посчитаем суммарные расход и энтальпию всех подводов до горла СА
                    H0=(H0*G0+hbld*Gbld)/(G0+Gbld)
                    G0+=Gbld

        return H0, G0, mass_comp_bld, R_bld

#    ФУНКЦИЯ ДЛЯ РАСЧЕТА ПАРАМЕТРОВ ВДУВОВ в турбину после горла СА
    def calculate_bleedin_after_turbine_throttle(self,device,Greference): #device - узел в котором считается вторичк
#        self.Gref_var=Greference
        #нужно рассчитать параметры воздуха вдуваемого: T, Mass_comp, H, R, G
        Gmid, G1=0,0 #суммарный расход вдувов
        Hmid, H1=0,0 #суммарная энтальпия вдувов
        Nbld=0 #суммарная мощность вырабатываемая вдувами на турбине (за исключением вдувов до горла)
#        mass_comp_bld=self.air_bleed_out[0]['mass_comp'][0]#инициализация пустого значения, чтобы питон не ругался - надо будет переделать по человечески
        mass_comp_bld=np.zeros(self.air_bleed_out[0]['mass_comp'][0].shape)
        R_bld=0
        #bleed_out_instance = [0)number_of_bleed_out/1)from/2)P_rel_from/3)h_rel_from/4)T_rel_from/5)G_rel_from/6)G_abs_from/7)A_from/8)F_from/9)G/10)h_from/11)T_from/12)P_from]
        #bleed_in_instance = [0)number_of_bleed_out/1)to/2)P_rel_to/3)h_rel_to/4)T_rel_to5)G_rel_to/6)G_abs_to/7)A_to/8)F_to/9)G/10)h_to/11)T_to/12)P_to]               
        for bleed_in_instance in self.air_bleed_in:
            if bleed_in_instance['device_to'].item() is device: #ищем в списке вдувов имя данного узла, если находим, значит в этот узел производится вдув, проводим с ним расчет              
                P1=device.inlet.P
                P2=device.outlet.P
                _row_index=bleed_in_instance['N'].item()-1
                Pbld_0=self.air_bleed_out[_row_index]['P_from'].item() #bld_0 - параметры в точке отбора
                Tbld_0=self.air_bleed_out[_row_index]['T_from'].item()
                Hbld_0=self.air_bleed_out[_row_index]['h_from'].item()
                Gbld_0=self.air_bleed_out[_row_index]['G_from'].item()                    
                mass_comp_bld=self.air_bleed_out[_row_index]['mass_comp'][0]
                R_bld=td.R_mix(mass_comp_bld)
                    
#                name_of_device=self.id_names[bleed_in_instance['device_to'].item()]
                name_of_device=bleed_in_instance['device_to'].item().name
                #точка отбора может быть задана относительным давлением, энтальпией или температурой. Далее извлекаем из массива bleed_in_instance чем задан отбор в данном случае и в зависимости от этого считаем параметры в точке вдува
                if np.isfinite(bleed_in_instance['P_rel_to']): #если задано P_rel_from 
                    if bleed_in_instance['P_rel_to']>0: #точка вдува в турбину может быть задана только через P_rel_to и только если значение P_rel_to>0
                        if bleed_in_instance['P_rel_to']>1:
                            print('Давление в точке вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' задано неверно. Относительное давление не может больше 1.')
                            raise SystemExit
                        Pbld=P1+(P2-P1)*bleed_in_instance['P_rel_to'].item()      
                        if Pbld>Pbld_0:
                            solverLog.info('Давление в точке вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' больше, чем давление в точке отбора. Давление в точке вдува='+str(Pbld)+', давление в точке отбора='+str(Pbld_0))
                            solverLog.info('Искусственно задаем давление в точке вдува равным давлению в точке отбора. Если это сообщение появляется в финальной итерации, то возможна ошибка в расчете отбора.')
                            Pbld=Pbld_0
                            # raise SystemExit
                        #считаем, что в канале вторичной воздушной системы воздух изоэнтропически расширяется от начального давления в точке отбора Pbld_0 до давления в точке подвода Pbld
                        if self.bleed_expansion==True:
                            Tbld=td.T2_thru_P1T1P2(Pbld_0,Tbld_0,Pbld,mass_comp_bld,R_bld,200,Tbld_0+dT)
                            hbld=td.H(Tbld,mass_comp_bld)
                        else:
                            Tbld=Tbld_0
                            hbld=Hbld_0
                        #проверяем чем задана величина вдува, она может быть задана относительным расходом G_rel_to от величины отбора, абсолютным G_abs_to, площадью F_to или пропускной способностью A_to
                        if np.isfinite(bleed_in_instance['G_rel_to']):#если задано G_rel_to
                            Gbld=Gbld_0*bleed_in_instance['G_rel_to'].item()
                            bleed_in_instance['G_abs_to']=Gbld
                        elif np.isfinite(bleed_in_instance['G_abs_to']):#если задано G_abs_to
                            Gbld=bleed_in_instance['G_abs_to'].item()
                            bleed_in_instance['G_rel_to']=Gbld/Gbld_0
                            if bleed_in_instance['G_rel_to']>1:
                                print('Расход воздуха через вдув в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' больше, чем расход отбора, чего не может быть! Отбор='+str(Gbld_0)+', вдув='+str(Gbld))
                        elif np.isfinite(bleed_in_instance['A_to']):#если задано A_to
                            print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+'. Причина: пока что не реализован алгоритм задания величины отбора пропускной способностью G*T^0.5/P')
                            raise SystemExit
                        elif np.isfinite(bleed_in_instance['F_to']):#если задано F_to
                            print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+'. Причина: пока что не реализован алгоритм задания величины отбора площадью F')
                            raise SystemExit
                        else:
                            print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N']))
                            raise SystemExit

                        if bleed_in_instance['P_rel_to']>0 and bleed_in_instance['P_rel_to']<1:
                            #считаем работу вдуваемого воздуха в турбине. считаем, что этот воздух работает отдельно от газа в турбине  при расширении от Pbld до давления на выходе из турбины
                            _T_turbine_outlet_isentropic_bld=td.T2_thru_P1T1P2(Pbld,Tbld,P2,mass_comp_bld,R_bld,200,Tbld+dT)
                            _h_turbine_outlet_isentropic_bld=td.H(_T_turbine_outlet_isentropic_bld,mass_comp_bld)
                            _L_isentropic_bld=(hbld-_h_turbine_outlet_isentropic_bld)
                            _L_real_bld=_L_isentropic_bld*device.Efftt 
                            _h_turbine_outlet_real_bld=hbld-_L_real_bld
                            _Nbld=_L_real_bld*Gbld
                            Hmid=(Hmid*Gmid+_h_turbine_outlet_real_bld*Gbld)/(Gmid+Gbld)
                            Gmid+=Gbld
                            Nbld+=_Nbld #знак плюс, потому что мощность вырабатываемая подводом воздуха в турбину добавляется к общйе мощности, вырабатываемой турбиной
                        elif bleed_in_instance['P_rel_to']==1:
                            H1=(H1*G1+hbld*Gbld)/(G1+Gbld)
                            G1+=Gbld
                        bleed_in_instance['G_to']=Gbld
                        bleed_in_instance['h_to']=hbld
                        bleed_in_instance['T_to']=Tbld
                        bleed_in_instance['P_to']=Pbld
                        bleed_in_instance['mass_comp']=mass_comp_bld

        return Hmid, Gmid, H1, G1, mass_comp_bld, R_bld, Nbld

#    ФУНКЦИЯ ДЛЯ РАСЧЕТА ПАРАМЕТРОВ ВДУВОВ В КАНАЛ
    def calculate_bleedin_channel(self,device,Greference): #device - узел в котором считается вторичка
#        self.Gref_var=Greference
        #bleed_out_instance = [0)number_of_bleed_out/1)from/2)P_rel_from/3)h_rel_from/4)T_rel_from/5)G_rel_from/6)G_abs_from/7)A_from/8)F_from/9)G/10)h_from/11)T_from/12)P_from]
        #bleed_in_instance = [0)number_of_bleed_out/1)to/2)P_rel_to/3)h_rel_to/4)T_rel_to5)G_rel_to/6)G_abs_to/7)A_to/8)F_to/9)G/10)h_to/11)T_to/12)P_to]               
        G0,Gmid,G1=0,0,0 #расходы вдувов в начале, в середине и в конце узла соответственно
        H0,Hmid,H1=0,0,0 #энтальпии вдувов соответственно
#        mass_comp_bld=self.air_bleed_out[0]['mass_comp'][0]#инициализация пустого значения, чтобы питон не ругался - надо будет переделать по человечески
        mass_comp_bld=np.zeros(self.air_bleed_out[0]['mass_comp'][0].shape)
        R_bld=0
        for bleed_in_instance in self.air_bleed_in:
            if bleed_in_instance['device_to'].item() is device: #ищем в списке вдувов имя данного узла, если находим, значит проводим с ним расчет
                P1=device.inlet.P
                P2=device.outlet_ideal.P
                _row_index=bleed_in_instance['N'].item()-1
                Pbld_0=self.air_bleed_out[_row_index]['P_from'].item() #bld_0 - параметры в точке отбора
                if np.isnan(Pbld_0): #
                    Pbld_0=device.outlet.P
                Tbld_0=self.air_bleed_out[_row_index]['T_from'].item()
                if np.isnan(Tbld_0):
                    Tbld_0=device.inlet.T
                Hbld_0=self.air_bleed_out[_row_index]['h_from'].item()
                if np.isnan(Hbld_0):
                    Hbld_0=device.inlet.H
                Gbld_0=self.air_bleed_out[_row_index]['G_from'].item()                    
                if np.isnan(Gbld_0):
                    
                    Gbld_0=0.00000001
                mass_comp_bld=self.air_bleed_out[_row_index]['mass_comp'][0]
                if np.isnan(mass_comp_bld[0]):
                    mass_comp_bld=device.inlet.mass_comp
                R_bld=td.R_mix(mass_comp_bld)                   
#                name_of_device=self.id_names[bleed_in_instance['device_to'].item()]
                name_of_device=bleed_in_instance['device_to'].item().name
                #точка вдува в канал может быть задана только относительным давлением
                if np.isfinite(bleed_in_instance['P_rel_to']): #если задано P_rel_from (!!!пока не точно, но вроде бы если отбор не от компрессора и не от турбины, то лучше его через P_rel_from не задавать!!! - надо подумать и проверить)
                    if bleed_in_instance['P_rel_to']>1 or bleed_in_instance['P_rel_to']<0:
                        print('Давление в точке вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' задано неверно. Относительное давление не может больше 1 или меньше 0.')
                        raise SystemExit
                    Pbld=P1+(P2-P1)*bleed_in_instance['P_rel_to'].item()      
                    if Pbld>Pbld_0:
                        solverLog.info('Давление в точке вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' больше, чем давление в точке отбора. Давление в точке вдува='+str(Pbld)+', давление в точке отбора='+str(Pbld_0))
                        solverLog.info('Искусственно задаем давление в точке вдува равным давлению в точке отбора. Если это сообщение появляется в финальной итерации, то возможна ошибка в расчете отбора.')
                        Pbld=Pbld_0
#                        raise SystemExit
                    #считаем, что в канале вторичной воздушной системы воздух изоэнтропически расширяется от начального давления в точке отбора Pbld_0 до давления в точке подвода Pbld
                    if self.bleed_expansion==True:
                        Tbld=td.T2_thru_P1T1P2(Pbld_0,Tbld_0,Pbld,mass_comp_bld,R_bld,200,Tbld_0+dT)
                        hbld=td.H(Tbld,mass_comp_bld)
                    else:
                        Tbld=Tbld_0
                        hbld=Hbld_0
                else:
                    print('Давление в точке вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' задано неверно. Должно быть задано значение P_rel_to.')
                    raise SystemExit

                #проверяем чем задана величина отбора, она может быть задана относительным расходом G_rel_from, абсолютным G_abs_from, площадью F_from или пропускной способностью A_from
                if np.isfinite(bleed_in_instance['G_rel_to']):#если задано G_rel_to
                    Gbld=Gbld_0*bleed_in_instance['G_rel_to'].item()
                    bleed_in_instance['G_abs_to']=Gbld
                elif np.isfinite(bleed_in_instance['G_abs_to']):#если задано G_abs_to
                    Gbld=bleed_in_instance['G_abs_to'].item()
                    bleed_in_instance['G_rel_to']=Gbld/Gbld_0
                    if bleed_in_instance['G_rel_to']>1:
                        print('Расход воздуха через вдув в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+' больше, чем расход отбора, чего не может быть! Отбор='+str(Gbld_0)+', вдув='+str(Gbld))
                elif np.isfinite(bleed_in_instance['A_to']):#если задано A_to
                    print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+'. Причина: пока что не реализован алгоритм задания величины отбора пропускной способностью G*T^0.5/P')
                    raise SystemExit
                elif np.isfinite(bleed_in_instance['F_to']):#если задано F_to
                    print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N'])+'. Причина: пока что не реализован алгоритм задания величины отбора площадью F')
                    raise SystemExit
                else:
                    print('Неверно задана величина вдува в узел '+name_of_device+" от отбора №"+str(bleed_in_instance['N']))
                    raise SystemExit
                bleed_in_instance['G_to']=Gbld
                bleed_in_instance['h_to']=hbld
                bleed_in_instance['T_to']=Tbld
                bleed_in_instance['P_to']=Pbld
                bleed_in_instance['mass_comp']=mass_comp_bld
                if bleed_in_instance['P_rel_to']==0: #если отбор в начале узла
                    H0=(H0*G0+hbld*Gbld)/(G0+Gbld)
                    G0+=Gbld
                elif bleed_in_instance['P_rel_to']==1:  #если отбор в конце узла
                    H1=(H1*G1+hbld*Gbld)/(G1+Gbld)
                    G1+=Gbld
                elif bleed_in_instance['P_rel_to']>0 and bleed_in_instance['P_rel_to']<1:  #если отбор в середине узла
                    Hmid=(Hmid*Gmid+hbld*Gbld)/(Gmid+Gbld)
                    Gmid+=Gbld

        return G0,H0,Gmid,Hmid,G1,H1,mass_comp_bld, R_bld

                    
#    ФУНКЦИЯ ДЛЯ РАСЧЕТА ПАРАМЕТРОВ ОТБОРОВ КС и канала
    def calculate_bleedout_combustor_and_channel(self,device,Greference): #device - узел в котором считается вторичка, eff - кпд этого узла (если это компрессор или турбина, иначе = 1), G_ref - расход воздуха относительно которого задаются отборы (обычно расход на входе в компрессор), air_bleed_out,air_bleed_in - массивы отборов и вдувов
        #расчет всех отборов
#        self.Gref_var=Greference
        #bleed_out_instance = [0)number_of_bleed_out/1)from/2)P_rel_from/3)h_rel_from/4)T_rel_from/5)G_rel_from/6)G_abs_from/7)A_from/8)F_from/9)G/10)h_from/11)T_from/12)P_from]
        G0,Gmid,G1=0,0,0 #расходы отборов в начале, в середине и в конце узла соответственно
        for bleed_out_instance in self.air_bleed_out:
            if bleed_out_instance['device_from'].item() is device: #ищем в списке отборов имя данного узла, если находим, значит от этого узла производится отбор, проводим с ним расчет
                P1=device.inlet.P
                T1=device.inlet.T
                H1=device.inlet.H
                P2=device.outlet.P
                mass_comp_bld=device.inlet.mass_comp               
                #в канале и КС точка отбора может быть задана толоько относительным давлением. Далее извлекаем из массива bleed_out_instance чем задан отбор в данном случае и в зависимости от этого считаем параметры в точке отбора
                if np.isfinite(bleed_out_instance['P_rel_from']): 
                    Pbld=P1+(P2-P1)*bleed_out_instance['P_rel_from'].item()      
                    Tbld=T1
                    hbld=H1
                else:
                    print('Неверно задана точка отбора №'+str(bleed_out_instance['N']+'. В канале и камере сгорания точка отбора может задаваться только относительным давлением P_rel_from'))
                    raise SystemExit
                #проверяем чем задана величина отбора, она может быть задана относительным расходом G_rel_from, абсолютным G_abs_from, площадью F_from или пропускной способностью A_from
                if np.isfinite(bleed_out_instance['G_rel_from']):#если задано G_rel_from
                    Gbld=Greference*bleed_out_instance['G_rel_from'].item()*self.ident_G[bleed_out_instance['N'][0]] #крайний множитель - это увязочный коэффициент
                    bleed_out_instance['G_abs_from']=Gbld
                elif np.isfinite(bleed_out_instance['G_abs_from']):#если задано G_abs_from
                    Gbld=bleed_out_instance['G_abs_from'].item()**self.ident_G[bleed_out_instance['N'][0]] #крайний множитель - это увязочный коэффициент
                    bleed_out_instance['G_rel_from']=Gbld/Greference
                elif np.isfinite(bleed_out_instance['A_from']):#если задано A_from
                    print('Неверно задана величина отбора №'+str(bleed_out_instance['N'])+ '. Причина: пока что не реализован алгоритм задания величины отбора пропускной способностью G*T^0.5/P')
                    raise SystemExit
                elif np.isfinite(bleed_out_instance['F_from']):#если задано F_from
                    print('Неверно задана величина отбора №'+str(bleed_out_instance['N'])+ '. Причина: пока что не реализован алгоритм задания величины отбора площадью F')
                    raise SystemExit
                else:
                    print('Неверно задана величина отбора №'+str(bleed_out_instance['N']))
                    raise SystemExit
                bleed_out_instance['G_from']=Gbld
                bleed_out_instance['h_from']=hbld
                bleed_out_instance['T_from']=Tbld
                bleed_out_instance['P_from']=Pbld
                bleed_out_instance['mass_comp']=mass_comp_bld
                if bleed_out_instance['P_rel_from']==0: #если отбор в начале узла
                    G0+=-Gbld #знак минус, потому что это отбор от общего расхода через узел
                elif bleed_out_instance['P_rel_from']==1:  #если отбор в конце узла
                    G1+=-Gbld
                elif bleed_out_instance['P_rel_from']>0 and bleed_out_instance['h_rel_from']<1:  #если отбор в середине узла
                    Gmid+=-Gbld

        return G0,Gmid,G1

                  

    #далее два вспомогательные метода для преобразования данных по вторичной воздушной системе из строкового состояния от пользователя в массив для использования программой 
    #secondary_air_system_out - отборы, secondary_air_system_in - возвраты
    def bleed_out_str2mtrx(self,devices,bleed_out_str):
        #массив отборов в формате number_of_bleed_out/from/P_rel_from/h_rel_from/T_rel_from/G_rel_from/G_abs_from/A_from/F_from/G/h_from/T_from/P_from/mass_comp
        array_type=np.dtype([('N', np.int),('device_from', np.object),('P_rel_from', np.float),('h_rel_from', np.float),('T_rel_from', np.float),('G_rel_from', np.float),('G_abs_from', np.float),('A_from', np.float),('F_from', np.float),('G_from', np.float),('h_from', np.float),('T_from', np.float),('P_from', np.float),('mass_comp', np.float, td.Number_of_components)])
#        rezult=np.full(13,np.nan)
        rezult=np.full(1,np.nan,dtype=array_type)
        for temp_data1 in bleed_out_str:  #'1,lpc,T_rel_from=0.648,G_rel_from=0.003'
            temp_data2=temp_data1.split(',')
#            data=np.full(13,np.nan)#массив отборов в формате number_of_bleed_out/from/P_rel_from/h_rel_from/T_rel_from/G_rel_from/G_abs_from/A_from/F_from/G/h_from/T_from/P_from
            data=np.full(1,np.nan,dtype=array_type)
            #в этот массив заносим все данные характеризующие отбор, каждая строчка - отдельный отбор
#            data[0]=temp_data2[0]#number_of_bleed_out - номер отбора
            data['N']=temp_data2[0]
            #data[1]=id_names.index(temp_data2[1])#from - имя узла из которого производится отбор, преборазуем имя в id
#            data['device_from']=temp_data2[1]
            data['device_from']=devices[temp_data2[1]]
            temp_data3=temp_data2[2].split('=')#P_rel_from/h_rel_from/T_rel_from - смотрим какое из трех значений задано, это значение характеризует точку отбора, нельзя чтобы было задано более одного значения или 0
            if temp_data3[0]=="P_rel_from": #точка отбора задается относительным давлением, 0 - вход в узел, 1 - выход из узла
#                data[2]=temp_data3[1]
                data['P_rel_from']=temp_data3[1]
            elif temp_data3[0]=="h_rel_from": #точка отбора задается относительной энтальпией, 0 - вход в узел, 1 - выход из узла
#                data[3]=temp_data3[1]
                data['h_rel_from']=temp_data3[1]
            elif temp_data3[0]=="T_rel_from": #точка отбора задается относительной температурой, 0 - вход в узел, 1 - выход из узла
#                data[4]=temp_data3[1]
                data['T_rel_from']=temp_data3[1]
            else:
                print('Неверно задана точка отбора №'+str(data['N']))
                raise SystemExit
            temp_data3=temp_data2[3].split('=')    #G_rel_from/G_abs_from/A_from/F_from -  - смотрим какое из трех значений задано, это значение характеризует величину отбора, нельзя чтобы было задано более одного значения или 0
            if temp_data3[0]=="G_rel_from": #величина отбора задается относительным расходом воздуха
#                data[5]=temp_data3[1]
                data['G_rel_from']=temp_data3[1]
            elif temp_data3[0]=="G_abs_from": #величина отбора задается абсолютным (физическим) расходом воздуха
#                data[6]=temp_data3[1]
                data['G_abs_from']=temp_data3[1]
            elif temp_data3[0]=="A_from": #величина отбора задается пропускной способностью A=G*T^0.5/P
#                data[7]=temp_data3[1]
                data['A_from']=temp_data3[1]
            elif temp_data3[0]=="F_from": #величина отбора задается площадью поперечного сечения
#                data[8]=temp_data3[1]
                data['F_from']=temp_data3[1]
            else:
                print('Неверно задана величина отбора №'+str(data['N']))
                raise SystemExit
            if rezult.ndim==1 and rezult['N']<0:
                rezult=data #TODO!!! здесь есть баг! если в списке отборов есть только один отбор, то размеры конечного массива rezult равны (1), хотя должны быть ((1)), в итоге прога крашится - надо исправить. То же касательно возвратов. Возможно есть смысл использовать обычный словарь, а не сложный numpy array
            else:
                rezult=np.vstack((rezult,data))
        return rezult
        
    def bleed_in_str2mtrx(self,devices,bleed_in_str):
        #массив вдувов в формате number_of_bleed_out/to/P_rel_to/h_rel_to/T_rel_to/G_rel_to/G_abs_to/A_to/F_to/G/h_to/T_to/P_to/
        array_type=np.dtype([('N', np.int),('device_to', np.object),('P_rel_to', np.float),('h_rel_to', np.float),('T_rel_to', np.float),('G_rel_to', np.float),('G_abs_to', np.float),('A_to', np.float),('F_to', np.float),('G_to', np.float),('h_to', np.float),('T_to', np.float),('P_to', np.float),('mass_comp', np.float, td.Number_of_components)])
#        rezult=np.full(13,np.nan)
        rezult=np.full(1,np.nan,dtype=array_type)
        for temp_data1 in bleed_in_str:  #'1,outlet,h_rel_to=0,G_rel_to=1'
            temp_data2=temp_data1.split(',')
#            data=np.full(13,np.nan)#массив вдувов в формате number_of_bleed_out/to/P_rel_to/h_rel_to/T_rel_to/G_rel_to/G_abs_to/A_to/F_to/G/h_to/T_to/P_to/
            data=np.full(1,np.nan,dtype=array_type)
            #в этот массив заносим все данные характеризующие вдув, каждая строчка - отдельный вдув
#            data[0]=temp_data2[0]#number_of_bleed_out - номер отбора из которого ведется вдув
            data['N']=temp_data2[0]
#            data[1]=id_names.index(temp_data2[1])#to - имя узла из которого производится отбор, преборазуем имя в id
#            data['device_to']=id_names.index(temp_data2[1])
            data['device_to']=devices[temp_data2[1]]
            temp_data3=temp_data2[2].split('=')#P_rel_to/h_rel_to/T_rel_to - смотрим какое из трех значений задано, это значение характеризует точку вдува, нельзя чтобы было задано более одного значения или 0
            if temp_data3[0]=="P_rel_to": #точка вдува задается относительным давлением, 0 - вход в узел, 1 - выход из узла
#                data[2]=temp_data3[1]
                data['P_rel_to']=temp_data3[1]
            elif temp_data3[0]=="h_rel_to": #точка вдува задается относительной энтальпией, 0 - вход в узел, 1 - выход из узла
#                data[3]=temp_data3[1]
                data['h_rel_to']=temp_data3[1]
            elif temp_data3[0]=="T_rel_to": #точка вдува задается относительной температурой, 0 - вход в узел, 1 - выход из узла
#                data[4]=temp_data3[1]
                data['T_rel_to']=temp_data3[1]
            else:
                print('Неверно задана величина вдува в узел '+temp_data2[1]+' из отбора №'+str(data['N'])+'. Место вдува задается одним из возможных вариантов: P_rel_to=, h_rel_to= или T_rel_to=')
                raise SystemExit
            temp_data3=temp_data2[3].split('=')    #G_rel_to/G_abs_to/A_to/F_to -  - смотрим какое из трех значений задано, это значение характеризует величину вдува, нельзя чтобы было задано более одного значения или 0
            if temp_data3[0]=="G_rel_to": #величина вдува задается относительным расходом воздуха
#                data[5]=temp_data3[1] #TODO!!! в дальнейшем сюда нужно встроить функцию eval, чтобы пользователь мог задавать арифметическое выражение в исходных данных и оно здесь автоматом вычислялось, но нужно подумать над безопасностью
                data['G_rel_to']=temp_data3[1]
            elif temp_data3[0]=="G_abs_to": #величина вдува задается абсолютным (физическим) расходом воздуха
#                data[6]=temp_data3[1]
                data['G_abs_to']=temp_data3[1]
            elif temp_data3[0]=="A_to": #величина вдува задается пропускной способностью A=G*T^0.5/P
#                data[7]=temp_data3[1]
                data['A_to']=temp_data3[1]
            elif temp_data3[0]=="F_to": #величина вдува задается площадью поперечного сечения
#                data[8]=temp_data3[1]
                data['F_to']=temp_data3[1]
            else:
                print('Неверно задана величина вдува в узел '+temp_data2[1]+' из отбора №'+str(data['N'])+'. Место вдува задается одним из возможных вариантов: G_rel_to=, G_abs_to=, A_to= или F_to=')
                raise SystemExit
            if rezult.ndim==1 and rezult['N']<0:
                rezult=data
            else:
                rezult=np.vstack((rezult,data))
        return rezult
        
    def calculate(self,engine):#эта штука нужна чтобы обновлять значение ссылочного расхода на каждой итерации в процессе поискка корней уравнения, т.к. в питоне нельзя пеердать значение переменной через список параметров в функцию как ссылку- она передается по значению и соответственно не обновляется внутри класса при изменении исходной внешней переменной
#        if np.isfinite(self.section_for_Gref.G):
        
        
        self.Gref_var=engine.arguments['Gref']
        self.Gref_calc=self.section_for_Gref.G    
        self.Gref_error=(self.Gref_var-self.Gref_calc)/self.Gref_calc #невязка по сссылочному расходу
        
        engine.residuals[self.name_of_error]=self.Gref_error #фигачим невязку по заданному и расчетному значению ссылочного расхода
    


# test=CrossSection()
# test.mass_comp=np.array([7.5512e-01, 2.3150e-01, 1.2920e-02, 4.6000e-04, 0.0000e+00, 0.0000e+00, 0.0000e+00])
# test.T=1000
# test.P=500000
# # test.Ps=100000
# test.F=0.01
# test.G=50
# test.M=1
# #проверить как будет работать если задавать в качестве исходных данных скорость. Можно выделить три основных типа заадч: известен (помимо полных параметров) расход, статическое давление или скорость

# test.calculate()
# test.status()










#загружаем характеристику компрессора        
#name_of_file='compressor_map.dat'
#with open(name_of_file, 'rb') as f:
#    data_map = pickle.load(f)        
#n_map=data_map[0]
#betta_map=data_map[1]
#G_map=data_map[2]
#PR_map=data_map[3]
#Eff_map=data_map[4]
#Eff_f=(RectBivariateSpline( n_map,betta_map, Eff_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
#G_f=(RectBivariateSpline( n_map,betta_map, G_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
#PR_f=(RectBivariateSpline( n_map,betta_map, PR_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
#
##загружаем характеристику турбины
#name_of_file2='turbine_map.dat'
#with open(name_of_file2, 'rb') as f:
#    data_map2 = pickle.load(f)        
#t_n_map=data_map[0]
#t_betta_map=data_map2[1]
#t_cap_map=data_map2[2]
#t_PR_map=data_map2[3]
#t_Eff_map=data_map2[4]
#t_A_map=data_map2[5]
#t_L_map=data_map2[6]
#t_Eff_f=(RectBivariateSpline(t_n_map, t_betta_map, t_Eff_map, bbox=[min(t_n_map), max(t_n_map), min(t_betta_map), max(t_betta_map)], kx=3, ky=3, s=0))
#t_cap_f=(RectBivariateSpline(t_n_map, t_betta_map, t_cap_map, bbox=[min(t_n_map), max(t_n_map), min(t_betta_map), max(t_betta_map)], kx=3, ky=3, s=0))
#t_PR_f=(RectBivariateSpline(t_n_map, t_betta_map, t_PR_map, bbox=[min(t_n_map), max(t_n_map), min(t_betta_map), max(t_betta_map)], kx=3, ky=3, s=0))
#t_A_f=(RectBivariateSpline(t_n_map, t_betta_map, t_A_map, bbox=[min(t_n_map), max(t_n_map), min(t_betta_map), max(t_betta_map)], kx=3, ky=3, s=0))
#t_L_f=(RectBivariateSpline(t_n_map, t_betta_map, t_L_map, bbox=[min(t_n_map), max(t_n_map), min(t_betta_map), max(t_betta_map)], kx=3, ky=3, s=0))

def import_map_function(filename,maptype):
    with open(filename, 'rb') as f:
        data_map = pickle.load(f) 
    if maptype=='compressor':
        n_map=data_map[0]
        betta_map=data_map[1]
        G_map=data_map[2]
        PR_map=data_map[3]
        Eff_map=data_map[4]
        Eff_f=(RectBivariateSpline( n_map,betta_map, Eff_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        G_f=(RectBivariateSpline( n_map,betta_map, G_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        PR_f=(RectBivariateSpline( n_map,betta_map, PR_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        rezult=dict(Eff_function=Eff_f,
                    G_function=G_f,
                    PR_function=PR_f)
    elif maptype=='turbine':
        n_map=data_map[0]
        betta_map=data_map[1]
        G_map=data_map[2]
        PR_map=data_map[3]
        Eff_map=data_map[4]
        A_map=data_map[5]
        L_map=data_map[6]
        Eff_f=(RectBivariateSpline( n_map,betta_map, Eff_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        G_f=(RectBivariateSpline( n_map,betta_map, G_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        PR_f=(RectBivariateSpline( n_map,betta_map, PR_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        A_f=(RectBivariateSpline(n_map, betta_map, A_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        L_f=(RectBivariateSpline(n_map, betta_map, L_map, bbox=[min(n_map), max(n_map), min(betta_map), max(betta_map)], kx=3, ky=3, s=0))
        rezult=dict(Eff_function=Eff_f,
            G_function=G_f,
            PR_function=PR_f,
            Alfa_function=A_f,
            Lambda_function=L_f)
    return rezult

#test_rez=import_map_function('обработанные характеристики/2019-04-03 16_07 ОК ТВ7-117 v2_output.dat','compressor')

#входной контроль характеристик
"""
print("пример расчета:")
print(Eff_f(1,0.5),G_f(1,0.5),PR_f(1,0.5))
print(t_Eff_f(1,0.5),t_cap_f(1,0.5),t_PR_f(1,0.5),t_A_f(1,0.5),t_L_f(1,0.5))
fig, axes = plt.subplots(6,1)
fig.set_size_inches(15, 30)
n_v=np.arange(min(n_map), max(n_map)+0.00001,0.1)
betta_v=np.arange(0, 1.00001,0.1)
for n_i in n_v:
    G_v=[]
    PR_v=[]
    Eff_v=[]
    for betta_i in betta_v:
        G_v.append(float(G_f(n_i,betta_i)))
        PR_v.append(float(PR_f(n_i,betta_i)))
        Eff_v.append(float(Eff_f(n_i,betta_i)))
    axes[0].plot(G_v,PR_v,label=n_i)
    axes[0].legend()
    axes[1].plot(G_v,Eff_v,label=n_i)
    axes[1].legend()
axes[0].set_title('Хараткеристика компрессора PR=f(G)')
axes[0].legend()
axes[1].set_title('Хараткеристика компрессора Eff=f(G)')
axes[1].legend()
n_v2=np.arange(min(t_n_map), max(t_n_map)+0.00001,0.1)
betta_v2=np.arange(0, 1.00001,0.1)
for n_i in n_v2:
    G_v=[]
    PR_v=[]
    Eff_v=[]
    A_v=[]
    L_v=[]
    for betta_i in betta_v:
        G_v.append(float(t_cap_f(n_i,betta_i)))
        PR_v.append(float(t_PR_f(n_i,betta_i)))
        Eff_v.append(float(t_Eff_f(n_i,betta_i)))
        A_v.append(float(t_A_f(n_i,betta_i)))
        L_v.append(float(t_L_f(n_i,betta_i)))
    axes[2].plot(PR_v,G_v,label=n_i)
    axes[2].legend()
    axes[3].plot(PR_v,Eff_v,label=n_i)
    axes[3].legend()
    axes[4].plot(PR_v,A_v,label=n_i)
    axes[4].legend()
    axes[5].plot(PR_v,L_v,label=n_i)
    axes[5].legend()
axes[2].set_title('Хараткеристика турбины G=f(PR)')
axes[2].legend()
axes[3].set_title('Хараткеристика турбины Eff=f(PR)')
axes[3].legend()
axes[4].set_title('Хараткеристика турбины Alfa=f(PR)')
axes[4].legend()
axes[5].set_title('Хараткеристика турбины Lambda=f(PR)')
axes[5].legend()
"""


#проверяем как работают модули
#wet_air_test=np.array([0.749164,0.229674,0.012818,0.000456,0.007888,0,0])
#fuel_test=np.array([0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 0.0000e+00, 1.0000e+00])

#testinlet=CrossSection()    
#testinlet.P=350000
#testinlet.T=2100
#testinlet.Ps=93432
#testinlet.F=0.4902
#testinlet.G=86.9
#testinlet.mass_comp=RD33095
#testinlet.V=1500
#testinlet.V=400
#testinlet.capacity=0.0001
#testinlet.F=0.723823
#testinlet.F=0.176
#testinlet.mass_comp=dry_air_test
#testinlet.calculate()
#testinlet.status()


#channel_test=Channel(1,name='каналище')
#channel_test.inlet=testinlet
#channel_test.outlet.F=0.1
#channel_test.fi=0.95
#channel_test.calculate()
#channel_test.status()


#brn_test=Combustor(Sigma_map=1, Eff_map=1, inlet=testinlet, G_fuel=0.2, T_fuel=288.15, Th=300,mass_comp_fuel=fuel_test, Eff_dp=0.99, Ginlet_dp=53, Pinlet_dp=2600000, Tinlet_dp=685, Volume_burner=0.004,name='КС')
#brn_test.sigma=0.95
#brn_test=Combustor(Sigma_map=1, Eff_map=1, inlet=testinlet, G_fuel=0.1, T_fuel=350, Th=300, mass_comp_fuel=fuel_test, Eff_dp=0.99, Ginlet_dp=3, Pinlet_dp=1100000, Tinlet_dp=700, Volume_burner=0.004, name='brn'):       
#brn_test.calculate()
#brn_test.status()

#initial_data, upstream, name
#testCompr=Compressor(G_map=G_f,PR_map=PR_f,Eff_map=Eff_f,name='test_name',rotor=2)
#testCompr.inlet.P=100818.375
#testCompr.inlet.T=243.15
#testCompr.n_phys=1
#testCompr.T_inlet_design_point=288.15
#testCompr.P_inlet_design_point=100000
#testCompr.inlet.mass_comp=dry_air_test
##testCompr.inlet=testinlet
##testCompr.outlet.F1=0.1
#testCompr.calculate()
#testCompr.status()
#print(dir(testCompr.outlet))
#testCompr.inlet.status()
#testCompr.outlet.status()
#testTurb=Turbine(Capacity_map=t_cap_f, PR_map=t_PR_f, Eff_map=t_Eff_f, A_map=t_A_f, L_map=t_L_f, name='турбина', rotor=3)
#testTurb.inlet.T=1500
#testTurb.inlet.P=2000000
#testTurb.n_phys=1
#testTurb.inlet.mass_comp=dry_air_test
#testTurb.T_throttle_design_point=1400
#testTurb.T_inlet_design_point=1000000
#testTurb.throttle.F=0.006
#testTurb.calculate()
#testTurb.status()
#rezult_comb=Combustion_properties(dry_air_test, fuel_test,0.1, 10, 0.99)
#print(rezult_comb[0])
#print(rezult_comb[1])
#print(type(rezult_comb[2]))
#print(type([1,2,3]))
#print(rezult_comb[3])
#[L0, alfa, mass_comp_gas, R_comb_prod]
#print(CrossSection())
#print(td.H_JetALiquid(400)-td.H_JetALiquid(350))
#print(td.H_JetALiquid(400)-td.H_JetALiquid(300))
#print(td.H_JetALiquid(400)-td.H_JetALiquid(250))
#print(Gamma(10, 1000000, 500, 0.003207235))

"""
!!!Функции ниже стоит реализовать позже
void gas_data::calculate_V_real()
{
	if (isnan(V_real) && !isnan(V) && !isnan(speed_coef))
	{
		V_real = V*speed_coef;
	}
}

void gas_data::calculate_lambda_real()
{
	if (isnan(lambda_real) && !isnan(V_real) && !isnan(T) && !isnan(FAR) && !isnan(WAR) && !isnan(R))
	{
		lambda_real = V_real / Thermo.CriticalSpeed(T, FAR, WAR, R);
		was_edited = true;
	}
}

void gas_data::calculate_M_real()
{
	if (isnan(M_real) && !isnan(V_real) && !isnan(Tstatic_real) && !isnan(FAR) && !isnan(WAR) && !isnan(R))
	{
		M_real = V_real / Thermo.SoundSpeed(Tstatic_real, FAR, WAR, R);
		was_edited = true;
	}
}

void gas_data::calculate_viscosity()
{ //TODO! формулы для вычисления вязкости актуальны только до температуры 555К, это нужно исправить в дальнейшем!
	if (isnan(dynamic_viscosity) && !isnan(Tstatic_real)) //динамическая вязкость для воздуха!!!! получаемая размерность д.б. Па*с
	{
		dynamic_viscosity = 18.27e-6*(291.15 + 120) / (Tstatic_real + 120)*pow((Tstatic_real / 291.15), 1.5); //формула Сазерленда из википедии для воздуха
		/*эту формулу можно применять для температур в диапазоне 0 < T < 555 K и при давлениях менее 3,45 МПа
		с ошибкой менее 10 %, обусловленной зависимостью вязкости от давления.*/
		was_edited = true;
	};
	if (isnan(kinematic_viscosity) && !isnan(dynamic_viscosity) && !isnan(Rostatic_real)) 
	{
		kinematic_viscosity = dynamic_viscosity / Rostatic_real;  //
		was_edited = true;
	};
}
void gas_data::calculate_Re()
{
	if (isnan(Re) && !isnan(Rostatic_real) && !isnan(V_real) && !isnan(Dhydraulic) && !isnan(dynamic_viscosity))
	{
		Re = Rostatic_real*V_real*Dhydraulic / dynamic_viscosity;
		was_edited = true;
	}
}



"""




"""
описание их хелпа по Flow Simulator по типам вершин гидравлической схемы
3.3.1.1. Chamber Types

There are four main types of chambers in Flow Simulator: the Plenum, the Momentum, the Inertial and the Elevation chamber. There is also a Vortex chamber which is only used to store data for vortex segments.

The Plenum chamber is used to model a region in which there is no significant velocity head present. In this case any velocity head of flow entering the chamber is dissipated and the total pressure in the chamber is equal to the static pressure. The Plenum chamber is assumed to be rotating at the same speed as all of its attached elements. Therefore, all of its attached elements must be rotating at the same speed (or all elements can be stationary).

In the Momentum chamber, the mixed total pressure head of all flows entering the chamber is computed and resolved to give a vector flow direction. In this calculation, the direction of each incoming stream is defined by the element angles specified for the element from which the flow enters. Thereafter, according to the angular alignment of an element with flow leaving the chamber with this chamber flow direction, the appropriate component of total pressure in the direction of the element is used to drive flow from the chamber into the element. For non-rotating components, selection of the coordinate system directions relative to the engine axis is arbitrary where Momentum chambers are concerned since it is only the relative angle between elements that determines the inlet component of total pressure to each element. For rotating components the coordinate system direction is not arbitrary. The same θ and φ angle convention as used for inertial chambers should be used in order to calculate the correct swirl velocities. However, it is advisable to only use Momentum chambers when the swirl velocity is 0 (stationary components such as piping) or when the swirl velocity is the same as the metal rotation (XK=1, air is “onboard” the rotor).

The Momentum chamber is assumed to be rotating at the same speed as all of its attached elements. Therefore, all of its attached elements must be rotating at the same speed (or all elements can be stationary).

Momentum chambers are the foundation of Junction components and all relative angles must be set as equal when used in a junction. See the Components section for more information on the Junction component, and the Junction Element Calculations section for more information on the Junction element.

Caution must be used with Momentum chambers since the computed mixed total momentum is only valid for the total exit area of the elements having flow entering a downstream chamber. Flow Simulator assumes that the momentum of the mixing flows does not dissipate even if the downstream element(s) have a larger flow area than this. Another way of looking at this is that Flow Simulator assumes a perfect diffuser if the combined flow area of the downstream element inlets is greater than the combined exit areas of the upstream elements. The most often used, and valid, application of Momentum chambers is to connect Tube elements in cooling circuits of airfoils.

The Inertial chamber is used to model the effects of tangentially swirling air or relative tangential velocity differences between air and a rotor. The flow direction coordinates for Inertial chambers are three-dimensional and follow the convention, based on the definitions in the Coordinate System section, of Z as the axial direction, U as the tangential direction and R as the radial direction. The corresponding angles are θ in the tangential direction and φ in the radial direction.

The Inertial chamber must be used to connect elements rotating at different speeds.

The Vortex chamber was created to facilitate the new Vortex element type. No elements can use a vortex chamber as the upstream or downstream chamber. A Vortex chamber’s main use is to store data (XK, P, T) at vortex segments and stations. A Vortex chamber stores temperature in the absolute frame like an Inertial chamber.

The new chamber centric cavity modeling in Flow Simulator requires that a chamber be associated with each cavity. Only chambers in the absolute reference frame (inertial and vortex chambers) can be associated with a cavity.

"""
    