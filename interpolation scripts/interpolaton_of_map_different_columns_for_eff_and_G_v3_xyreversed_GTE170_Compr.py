# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 14:37:01 2019
@author: Sundukov
Алгоритм подготовки характеристик
Предназначение - обработка массива исходных данных характеристик для получения прямоугольного поля
 размером [обороты х бетта], где каждое из значений этого поля равно соответственно одному из параметров характеристики.
 Далее полученное поле планируется использовать в расчетной модели например с помощью функции Rbf или SmoothBivariateSpline или стоит еще
 посмотреть в сторону функций, работающих на структурированных сетках
"""
#TODO!!! сделать автиоматическую аппроксимацию, для этого нужно сделать расчет качества аппроксимации - т.е. отклонение результирующих точек от исходных - на основании этого рассчитать какой-то обощенный критерий, затем пытаться его минимизировать путем оптимизации: варьирования коэффициентами сглаживания и степенями полиномов
#TODO!!! нужно сделать так, что в области при бетта <0 и >1 экстраполяция происходила на основе поля точек, взятых при тех же оборотах, но при бетта от 0 до 1, т.е. наприемр если нужно вычислить точку при ,бетта = 1,2 и n=0,8, то мы сначала считаем какое-то количество точек при бетта =[0,1] и n=0.8, затем на основе этих полученных точек экстраполируем в нужную там точку
#TODO!!! как-то попробовать использовать вторую произхводную для оценки качества аппроксимации
#TODO!!! для экстраполяции напорных кривых можно для каждой отдельной ветки посчитать коэффициент b линейного уравнения по двум/трем крайним точкам. Точки считать на графиках G/PR/Eff=f(betta). Затем по полученному массиву b=f(n) сделать аппроксимацию и из э\той аппроксимации брать угловой коэффициент на основе которого получать точки в области экстраполяции, задавая значения бетта от граничного значения (т.е. 0 или 1 ) и приабавляя к нему (или вычитая) какое-то фикс значение бетта, например 0,1. т.е. напримпаер задаем бетта = 0, -0,1, -0,2, -0,3 и 1, 1,1, 1,2, 1,3
#TODO!!! глобально! может пригодитсяь в других проектах. Иногда бывает проблема, что аппроксимируемая функция имеет координаты х которые не все время идут в порядке возрастания/убывания, и из-за этого вроде бы выгодно поменять местами x и y, но это тоже неудобно из-за того, что в дальнейшем возникает путаница между xи y. Нужно сделать так, чтобы при аппроксимации точек функцией и последующем поиске значений бетта осуществлялся поворот точек на какой угол (угол нужно найти) так, чтобы все х лежали более менее горизонтально и в порядке возрастания

"""
ОБЩИЙ АЛГОРИТМ РАБОТЫ:
    1) предварительно создать файл с данными характеристики, обычно это файл csv с колонками n;G;PR;Eff 
    2) указать имя файла в параметре name_of_file
    3) указать тип характеристик - компрессор ("compressor") или турбина ("turbine") в параметре type_of_map
    4) далее алгоритм программы строит отдельно для каждой ветки оборотов отдельно для параметров G;PR;Eff зависимость от параметра бетта, где бетта - условный вводимый нами  для удобства параметр.
    он может изменятсья от 0 до 1, т.е. 0 и 1 соответствуют крайним положениям на кривых, промежучтоные значения соответствуют промежуточным положениям на кривых.
    в конечном итоге мы получаем три графика зависимости G=f(betta), PR=f(betta), Eff=f(betta)
    5)глядя на эти графики мы контролируем их плавность/адекватность/физичность. Не должно быть никаких резких скачков. Для интерполяции исходных точек в идеале может использоваться функция  Akima1DInterpolatorModified,
    кривая, заданная этой функцией, проходит точно через заданные исходные точки не сглаживая их. Но очень часто необходимо сглаживание, т.к. исходные точки обычно подколбашивает вверх-вниз, поэтому разумнее использовать другую интерполирующую функцию - UnivariateSplineModified, 
    эта функция хороша тем, что при ее использовании можно задавать параметр s характеризующий сглаживание кривой (обычно если необходимо минимальное сглаживание, то s = 0.000001 или около того, для сильного сглаживания s=0.1-0.01 или даже больше)
    В общем если все ветки интерполируются хорошо, то это хорошо, если нет и сглаживание не помогает, то нужно детально рассматривать ситуацию.
    6)Также дополнительно указанные в предыдущем пункте функции строят график зависимости G=f(PR) тоже для каждой ветки. Их тоже стоит проконтролировать из тех же соображений, что и выше. А также с точки зрения того, чтобы они хорошо экстраполировались за пределами исходных данных.
    "Хорошо" в данном случае = более менее линейно, чтобы не было резких изменений/скачков/странностей.
    7) после того, как мы убедились, что интерполирующие функции G=f(betta), PR=f(betta), Eff=f(betta) работают удовлетваорительно присутпаем к следующему этапу интерполяции: теперь мы проходимся по всему диапазону значений бетта от 0 до 1 с некоторым шагом от минимальных оборотов n до максимальных. Для каждого значения бетта
    исходя из полученных выше функций строим функции G=f(n), PR=f(n), Eff=f(n). И по аналогии с пунктами 5 и 6 контролируем качество интерполяции: опять же мы можем варьировать параметром сглаживания s и типом интерполирующей функции (но лучше все же в качестве интерполирующей использовать UnivariateSplineModified, либо какую-нибудь подобную, которая умеет сглаживать неровности)
    8) если все нормас и нас все устраивает, то формируем массив данных в диапазоне оборотов n от минимальных до максимальных, и в диапазоне бетта от min до max, полученный массив сохраняем в файл (используем для этого библиотеку pickle). Этот файл - является результатом работы программы, т.е. далее он используется в термодинамической модели.
    Для проверки того, что полученный файл нормальный - строим различные проверочные графики, где сравниваются исходные точки и результирующая функция.
    
"""

import makecharts as chart
import pandas as pd
import numpy as np
import pickle
from matplotlib import pyplot as plt
from scipy.interpolate import Akima1DInterpolator
#from scipy.interpolate import BarycentricInterpolator
#from scipy.interpolate import KroghInterpolator
#from scipy.interpolate import PchipInterpolator
from scipy.interpolate import interp1d
from scipy.interpolate import CubicSpline
from scipy.interpolate import UnivariateSpline
#from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.optimize import brentq
from scipy.optimize import fsolve
from scipy.optimize import root, root_scalar, minimize, fmin
from scipy.interpolate import RectBivariateSpline
from mpl_toolkits.mplot3d import Axes3D
#from sklearn.linear_model import LinearRegression
import datetime
import os
from scipy.spatial.transform import Rotation

directory_to_save_pics="/plots/"

#3.6) модифицируем класс для построения сплайна Акимы таким образом, чтобы на концах сплайна кривая экстраполировалась по касательной    
class Akima1DInterpolatorModified(Akima1DInterpolator):
    def __call__(self, xx):
        if xx<self.x[0]:
            k=super(Akima1DInterpolatorModified, self).__call__(self.x[0],nu=1)
            b=self.__call__(self.x[0])
            rez=b+k*(xx-self.x[0])
        elif xx>self.x[-1]:
            k=super(Akima1DInterpolatorModified, self).__call__(self.x[-1],nu=1)
            b=self.__call__(self.x[-1])
            rez=b+k*(xx-self.x[-1])            
        else:
            rez=super(Akima1DInterpolatorModified, self).__call__(xx, nu=0, extrapolate=None)
        return rez    
#3.7) модифицируем класс для построения сплайна таким образом, чтобы на концах сплайна кривая экстраполировалась по касательной    
class UnivariateSplineModified(UnivariateSpline):
    def __init__(self,x,y,**kwargs):
        #исходная функция UnivariateSpline немного скорректирована таким образом, чтобы получаемыке исходные массивы x и y продлевались по краям вдоль линейной регресии на основе трех крайних точек, затем полученные дополнительные точки передаются в оригинальную функцию UnivariateSpline, которая уже рисует сплайн, используемый в дальнейшем
        if isinstance(x,pd.Series) or isinstance(x,np.ndarray) or isinstance(x,tuple):
            x=list(x)
        if isinstance(y,pd.Series) or isinstance(y,np.ndarray) or isinstance(y,tuple):
            y=list(y)           
        x0=x[:2] #!!! иногда полезно варьировать количеством точек на основе которых этот алгоримт экстраполирует функцию! 
        y0=y[:2]
        x1=x[-2:]
        y1=y[-2:]
        lin0=np.poly1d(np.polyfit(x0,y0,1))
        lin1=np.poly1d(np.polyfit(x1,y1,1))
        
        x0_new=np.linspace(-0.5+x[0],-0.1+x[0],5).tolist()
        x1_new=np.linspace(0.1+x[-1],0.5+x[-1],5).tolist()
        y0_new=lin0(x0_new).tolist()
        y1_new=lin1(x1_new).tolist()
        x=x0_new+x+x1_new
        y=y0_new+y+y1_new
        super().__init__(x,y,**kwargs)
        
    def __call__(self, val):
        x0=self._data[0][0]
        x1=self._data[0][-1]
        val=float(val)
        if isinstance(val,list) or isinstance(val,np.ndarray):
            rez=[]
            for xx in val:
                if xx<x0:   
                    k=super().__call__(x0,nu=1)
                    b=self.__call__(x0)
                    _rez=b+k*(xx-x0)
                elif xx>x1:
                    k=super().__call__(x1,nu=1)
                    b=self.__call__(x1)
                    _rez=b+k*(xx-x1)            
                else:
                    _rez=super().__call__(xx, nu=0)
                rez.append(float(_rez))
        elif isinstance(val,float):
            xx=val
            if xx<x0:   
                k=super().__call__(x0,nu=1)
                b=self.__call__(x0)
                rez=b+k*(xx-x0)
            elif xx>x1:
                k=super().__call__(x1,nu=1)
                b=self.__call__(x1)
                rez=b+k*(xx-x1)            
            else:
                rez=float(super().__call__(xx, nu=0))
        return rez    






DATA={} #для удобства тут будем хранить всю самую важную инфу

now = datetime.datetime.now()
date_text=now.strftime("%Y-%m-%d %H_%M")
#0) выбор типа характеристики: турбина или компрессор
# type_of_map="turbine" #!!!
type_of_map="compressor" #!!!
# name_of_file="turbine_jetcat_CFD_map_Kosmatov_Alexander_2019_12_reduced.csv"#!!!указать файл
name_of_file="2020 11 аэродинамические характеристики компрессора ГТЭ-170 по результатам CFD\AC CFD 2020 11 A+3.csv"#!!!указать файл
# name_of_file="2020 11 аэродинамические характеристики компрессора ГТЭ-170 по результатам CFD\AC CFD 2020 11 A-16.8.csv"#!!!указать файл
# name_of_file="turbine_jetcat_CFD_map_Kosmatov_Alexander_2019_12_reduced.csv"
#1)импорт данных
with open(os.getcwd()+"\\исходники характеристик\\"+name_of_file) as initial_data: 
    reader = pd.read_csv(initial_data, delimiter=';', decimal=',')

#1.2)проверяем, чтобы степени повышения/понижения давления не были указаны в диапазоне от 0 до 1
def func1(x):
    return (1/x)
if reader.PR[0]<1:
    reader['PR'] = reader['PR'].apply(func1)
#1.21)!!! проверяем чтобы все единицы были в СИ, при необходимости корректируем вручную здесь
# def func2(x):
#     return x/1000000
# reader['G']=reader['G'].apply(func2)
#1.22)!!! КПД д.б. в диапазоне от 0 до 1
# def func3(x):
#     return x/100
# reader['Eff']=reader['Eff'].apply(func3)

#1.3) добавляем параметр k, по которому дальше будем сортировать 
if type_of_map=="turbine":
    reader['k']=reader.PR
    reader['Gn']=reader.G*reader.n
if type_of_map=="compressor":
    reader['k']=reader.PR/reader.G
#1.31) приводим G и PR к относительному виду
#сначала сохраняем максимальные значения для каждого столбца данных
scales={'PR':reader.PR.max(),'G':reader.G.max(),'Eff':reader.Eff.max()}
DATA['abs_scales']=scales
if type_of_map=="turbine":
    scales.update({'A':reader.A.max(),'L':reader.L.max(),'Gn':reader.Gn.max()})
reader['Grel']=reader['G'].apply(lambda x: x/scales['G'])
reader['PRrel']=reader['PR'].apply(lambda x: x/scales['PR'])
reader['Effrel']=reader['Eff'].apply(lambda x: x/scales['Eff'])
if type_of_map=="turbine":
    reader['Arel']=reader['A'].apply(lambda x: x/scales['A'])
    reader['Lrel']=reader['L'].apply(lambda x: x/scales['L'])
    reader['Gnrel']=reader['Gn'].apply(lambda x: x/scales['Gn'])

DATA['reader']=reader

#1.4)при необходимости сортируем сначала в порядке возрастания оборотов, потом по параметру k в поярдке возрастания, потом в порядке убывания для G
#потом в порядке возрастаения степенеи повышения/понижения давления - стоит проверить получившийся результат
reader.sort_values(['n','k','G'],ascending=[True,True,False],inplace=True)
reader=reader.reset_index(drop=True)

"""3) далее характеристика будет представлена в виде поля зависимости G, PR, Eff от оборотов n и бетта-коэффициента.
Бетта-коэффициент характеризует вспомогательную кривую. Бетта=0 соответствует кривой проходящей через нижние точки (PR=min) кривых n=const
Бетта=1 соответствует кривой проходящей через верхние точки (PR=max) кривых n=const.
Далее сформируем векторы, которые будут содержать координаты, соответствующие кривым бетта=0 и бетта=1
"""
#3.1)из массива n достанем величины оборотов
rotations=pd.unique(reader.n) 
DATA['rotations']=rotations
#3.2) альтернативный метод (см.другое описание пункта 3.2 ниже): создаем две кривые на основе крайних точек каждой напорной кривой. Кривые характеризуют бетта=0 и бетта=1. Кривые создаются путем натягивания уравнния параболы на крание точки напорных кривых
#извлечем крайние точки напорных кривых
HighCurveX=[] #в этой штуке и в нижне йбудут храниться координаты крайних точка от каждой ветки оборотов
HighCurveY=[]
LowCurveX=[]
LowCurveY=[]
for nx in rotations:
    temp_data=reader.loc[reader.n == nx]
    if type_of_map=="turbine":
        HighCurveX.append(temp_data.PRrel.iloc[-1])
        HighCurveY.append(temp_data.Gnrel.iloc[-1])
        LowCurveX.append(temp_data.PRrel.iloc[0])
        LowCurveY.append(temp_data.Gnrel.iloc[0])
    elif type_of_map=="compressor":
        HighCurveY.append(temp_data.PRrel.iloc[-1])
        HighCurveX.append(temp_data.Grel.iloc[-1])
        LowCurveY.append(temp_data.PRrel.iloc[0])
        LowCurveX.append(temp_data.Grel.iloc[0])

#вспомогательная функция для поиска точки на кривой, максимальной бблизкой к заданной точке
def find_pnt(func,pnt): #здесь func - функция кривой, pnt - список с координатами заданной точки
    dist=lambda x: ((pnt[0]-x)**2+(pnt[1]-func(x))**2)**0.5
    rez=minimize(dist,pnt[0])
    x=rez['x']
    return float(x),func(float(x))


#натянем параболу на крайние точки  
#!!!!! здесь каждый раз нужно смотреть, чтобы кривые, описывающие крайние точки напорных веток не пересекались друг сдругом. Пока что это можно контролировать только вручную если задавать опорные точки
# LowCurveX.append(0.5),LowCurveY.append(0.15) #!!!!!эту точку добавляем вручную
# LowCurveX.insert(0,0.5),LowCurveY.insert(0,0.15) #!!!!!эту точку добавляем вручную
# LowCurveX.insert(0,1.5),LowCurveY.insert(0,1.05) #!!!!!эту точку добавляем вручную
# LowCurveX.insert(0,1),LowCurveY.insert(0,1.01) #!!!!!эту точку добавляем вручную
# HighCurveX.insert(0,2),HighCurveY.insert(0,1.8) #!!!!!эту точку добавляем вручную
# HighCurveX.insert(0,1.5),HighCurveY.insert(0,1.6) #!!!!!эту точку добавляем вручную
# HighCurveX.insert(0,1),HighCurveY.insert(0,1.4) #!!!!!эту точку добавляем вручную
# HighCurve=np.poly1d(np.polyfit(HighCurveY,HighCurveX,2)) #NB! тк кривая близка к вертикальной, то здесь удобно поменять местами x и y и соответственнно дальнейшее использование этих функций
# LowCurve=np.poly1d(np.polyfit(LowCurveY,LowCurveX,2))
HighCurve=np.poly1d(np.polyfit(HighCurveX,HighCurveY,2)) #NB! тк кривая близка к вертикальной, то здесь удобно поменять местами x и y и соответственнно дальнейшее использование этих функций
LowCurve=np.poly1d(np.polyfit(LowCurveX,LowCurveY,2))
# LowCurve=np.poly1d(np.polyfit([1.45, 1.75, 2.1],[0.05, 0.15, 0.25],1))
# HighCurve=np.poly1d(np.polyfit([3.95, 4.25, 4.6],[0.05, 0.15, 0.25],1))
# LowCurve=UnivariateSplineModified([1.4280000000000001, 1.8005000000000002, 1.953],[0.280594, 0.132936, 0.035278000000000004],k=2,s=0.0)
# HighCurve=UnivariateSplineModified([3.458, 4.05000000000003, 4.398],[0.038286, 0.14369600000000002, 0.24910600000000002],k=2,s=0.0)

#найдем минимальное, среднее и максимальное значения PR на основе полученных выше точек  
Xlowmin=LowCurveX[0];Xlowmax=LowCurveX[-1];Xlowmid=(Xlowmin+Xlowmax)/2
Ylowmin=LowCurveY[0];Ylowmax=LowCurveY[-1];Ylowmid=(Ylowmin+Ylowmax)/2
Xhighmin=HighCurveX[0];Xhighmax=HighCurveX[-1];Xhighmid=(Xhighmin+Xhighmax)/2
Yhighmin=HighCurveY[0];Yhighmax=HighCurveY[-1];Yhighmid=(Yhighmin+Yhighmax)/2

#глобальные минимум и максимум
Xmin=min(min(HighCurveX),min(LowCurveX))
Xmax=max(max(HighCurveX),max(LowCurveX))
Ymin=min(min(HighCurveY),min(LowCurveY))
Ymax=max(max(HighCurveY),max(LowCurveY))

#находим точки самые близкие к крайним на кривых LowCurve и HighCurve
Xlowmincrv,Ylowmincrv=find_pnt(LowCurve,[Xlowmin,Ylowmin])
Xlowmaxcrv,Ylowmaxcrv=find_pnt(LowCurve,[Xlowmax,Ylowmax])
Xlowmidcrv,Ylowmidcrv=find_pnt(LowCurve,[Xlowmid,Ylowmid])
# Ylowmincrv,Xlowmincrv=find_pnt(LowCurve,[Ylowmin,Xlowmin])
# Ylowmaxcrv,Xlowmaxcrv=find_pnt(LowCurve,[Ylowmax,Xlowmax])
# Ylowmidcrv,Xlowmidcrv=find_pnt(LowCurve,[Ylowmid,Xlowmid])
Xhighmincrv,Yhighmincrv=find_pnt(HighCurve,[Xhighmin,Yhighmin])
Xhighmaxcrv,Yhighmaxcrv=find_pnt(HighCurve,[Xhighmax,Yhighmax])
Xhighmidcrv,Yhighmidcrv=find_pnt(HighCurve,[Xhighmid,Yhighmid])
# Yhighmincrv,Xhighmincrv=find_pnt(HighCurve,[Yhighmin,Xhighmin])
# Yhighmaxcrv,Xhighmaxcrv=find_pnt(HighCurve,[Yhighmax,Xhighmax])
# Yhighmidcrv,Xhighmidcrv=find_pnt(HighCurve,[Yhighmid,Xhighmid])

#Проверяем все, что насчитали выше на графике #NB! x и y поменяны местами, смотри выше примечание к HighCurve
x=np.linspace(Xmin*0.8,Xmax*1.1,100)
y=np.linspace(Ymin*0.8,Ymax*1.1,100)
x_high=np.linspace(min(HighCurveX)*0.8,max(HighCurveX)*1.1,100)
x_low=np.linspace(min(LowCurveX)*0.8,max(LowCurveX)*1.1,100)
# x_high=HighCurve(y)
# x_low=LowCurve(y)
y_high=HighCurve(x_high)
y_low=LowCurve(x_low)

if type_of_map=="turbine":
    points_for_scatter=[{'x':reader.PRrel,'y':reader.Gnrel,'label':'исходные данные','s':1},
                    {'x':HighCurveX,'y':HighCurveY,'label':'верхние крайние точки','s':10,'marker':'x','c':'red'},
                    {'x':LowCurveX,'y':LowCurveY,'label':'нижние крайние точки','s':10,'marker':'x','c':'blue'},
                    {'x':[Xlowmin,Xlowmid,Xlowmax],'y':[Ylowmin,Ylowmid,Ylowmax],'label':'нижние опорные точки','s':20,'marker':'o','c':'black'},
                    {'x':[Xlowmincrv,Xlowmidcrv,Xlowmaxcrv],'y':[Ylowmincrv,Ylowmidcrv,Ylowmaxcrv],'label':'нижние опорные точки на кривой','s':30,'marker':'+','c':'black'},
                    {'x':[Xhighmin,Xhighmid,Xhighmax],'y':[Yhighmin,Yhighmid,Yhighmax],'label':'верхние опорные точки','s':20,'marker':'o','c':'black'},
                    {'x':[Xhighmincrv,Xhighmidcrv,Xhighmaxcrv],'y':[Yhighmincrv,Yhighmidcrv,Yhighmaxcrv],'label':'верхние опорные точки на кривой','s':30,'marker':'+','c':'black'}]
    # points_for_plot=[]
    points_for_plot=[{'x':x_high,'y':y},
                      {'x':x_low,'y':y},]   
elif type_of_map=="compressor":
    points_for_scatter=[{'x':reader.Grel,'y':reader.PRrel,'label':'исходные данные','s':1},
                    {'x':HighCurveX,'y':HighCurveY,'label':'верхние крайние точки','s':10,'marker':'x','c':'red'},
                    {'x':LowCurveX,'y':LowCurveY,'label':'нижние крайние точки','s':10,'marker':'x','c':'blue'},
                    {'x':[Xlowmin,Xlowmid,Xlowmax],'y':[Ylowmin,Ylowmid,Ylowmax],'label':'нижние опорные точки','s':20,'marker':'o','c':'black'},
                    {'x':[Xlowmincrv,Xlowmidcrv,Xlowmaxcrv],'y':[Ylowmincrv,Ylowmidcrv,Ylowmaxcrv],'label':'нижние опорные точки на кривой','s':30,'marker':'+','c':'black'},
                    {'x':[Xhighmin,Xhighmid,Xhighmax],'y':[Yhighmin,Yhighmid,Yhighmax],'label':'верхние опорные точки','s':20,'marker':'o','c':'black'},
                    {'x':[Xhighmincrv,Xhighmidcrv,Xhighmaxcrv],'y':[Yhighmincrv,Yhighmidcrv,Yhighmaxcrv],'label':'верхние опорные точки на кривой','s':30,'marker':'+','c':'black'}]
    # points_for_plot=[]
    points_for_plot=[{'x':x_high,'y':y_high},
                      {'x':x_low,'y':y_low},]
    
  #график с исходными данными  
_fig=chart.Chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,figure_size=(14,18),title='Первичная обработка исходных данных')

if type_of_map=="turbine":
    plt.ylim(min(reader.Gnrel)*0.1,max(reader.Gnrel)*1.2)

#сделаем функцию, которая на основе вспомогательного параметра бетта (0-1) будет вычислять три ключевых точки, на основе которых будет строиться новая парабола для указанного бетта
#функция на выходе выдает полином, которому можно скормить переменную x
def BettaCurve(betta):
    Ybettamin=Ylowmincrv+betta*(Yhighmincrv-Ylowmincrv)
    Ybettamid=Ylowmidcrv+betta*(Yhighmidcrv-Ylowmidcrv)
    Ybettamax=Ylowmaxcrv+betta*(Yhighmaxcrv-Ylowmaxcrv)
    Xbettamin=Xlowmincrv+betta*(Xhighmincrv-Xlowmincrv)
    Xbettamid=Xlowmidcrv+betta*(Xhighmidcrv-Xlowmidcrv)
    Xbettamax=Xlowmaxcrv+betta*(Xhighmaxcrv-Xlowmaxcrv)
    _x=np.append(Xbettamin,[Xbettamid,Xbettamax])
    _y=np.append(Ybettamin,[Ybettamid,Ybettamax])
    return np.poly1d(np.polyfit(_x,_y,2))


#проверяем чтобы функция bettacurve правильно строила промежуточные кривые. Достраиваем на графике бетта-кривые
cmap = plt.get_cmap('jet') #используем палитру jet из матплотлиба
colors = [cmap(i) for i in np.linspace(0, 1, 9)]

for _i_color in zip(np.linspace(-0.5, 1.5, 9),colors):
    i=_i_color[0]
    color=_i_color[1]
    y_betta=BettaCurve(i)(x)
    _fig.figure.axes[0].plot(x,y_betta,'--r',label='Betta='+str(i),color=color)
    _fig.figure.axes[0].legend()



#4) сформируем векторы G_output, PR_output и Eff_output, где каждый элемент вектора- функция зависимости соответствующего параметра от бетта при различных значениях оборотов из вектора rotations

def f_factory(func,val,val2=0):#вспомогательная фабрика функций (https://stackoverflow.com/questions/3431676/creating-functions-in-a-loop)
    def f(x):           #сначала я пытался создавать функции внутри цикла ниже, но так не работает, поскольку переменные внутри функции читаются на момент обращения к этой функции, а не на момент ее объявления
        return func(x)*val+val2  # i is now a *local* variable of f_factory and can't ever change
    return f   

slopes_G_low=[]
slopes_PR_low=[]
slopes_Eff_low=[]
slopes_G_high=[]
slopes_PR_high=[]
slopes_Eff_high=[]
slopes_Gn_low=[]
slopes_Gn_high=[]
slopes_L_low=[]
slopes_L_high=[]
slopes_A_low=[]
slopes_A_high=[]
# maxs_G=[]
# maxs_PR=[]
# maxs_Eff=[]
# maxs_Gn=[]
# maxs_L=[]
# maxs_A=[]
bettas=pd.Series(dtype=float)

#проходимся по всем заданным веткам оборотов, находим угловые коэффициенты k линейного уравнения kx+b на каждой ветке оборотов, на верхнем и нижнем краях этой ветки оборотов на основе n крайних точек (т.е. по трем точкам  создаем линейную регрессию и из регрессии находим угловой коэффициент)
#помио этого в массиве reader добалвем дополнительные параметры при необходимости и приводим их в относительный вид (нормализуем от носительно максимума на каждой ветке). Максимумы каждой ветке сохраняем в массиве вида "maxs_..."
reader['betta']=np.nan
for ni in rotations:
    temp_data=reader.loc[reader.n == ni] #выделяем из общего массива данных только те, что относятся к определенным оборотам nx
    G_temp=temp_data.G
    Eff_temp=temp_data.Eff
    PR_temp=temp_data.PR        
    # max_Eff=max(Eff_temp)
    # min_G=G_temp.min()  
    # max_G=(G_temp-min_G).max()
    # max_PR=PR_temp.max()
    # G_temp=(G_temp-min_G)/max_G #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются
    # PR_temp=PR_temp/max_PR #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются
    # Eff_temp=Eff_temp/max_Eff
    #массив кпд нормализовать не обязательно, т.к. он по умолчанию всегда чуть менее 1 
    if type_of_map=="turbine":
        k_temp=PR_temp
        Gn_temp=temp_data.Gn
        # max_Gn=Gn_temp.max()
        # Gn_temp=Gn_temp/max_Gn
        if "L" in temp_data:
            L_temp=temp_data.L
            # max_L=L_temp.max()
            # L_temp=L_temp/max_L
        if 'A' in temp_data:
            A_temp=temp_data.A
            # max_A=A_temp.max()
            # A_temp=A_temp/max_A
    elif type_of_map=="compressor":
        k_temp=PR_temp/G_temp
    Betta_temp=[]
    
    if type_of_map=="turbine":
        for XY in temp_data.loc[:,['PRrel','Gnrel']].values:
            X_PR=XY[0];Y_Gn=XY[1]
            _func=lambda betta: BettaCurve(betta)(Y_Gn)-X_PR
            _betta=root(_func,x0=0.5)['x'][0]
            Betta_temp.append(_betta)
    elif type_of_map == "compressor":
        for XY in temp_data.loc[:,['PRrel','Grel']].values:
            X_G=XY[1];Y_PR=XY[0]
            _func=lambda betta: BettaCurve(betta)(X_G)-Y_PR
            _betta=root(_func,x0=0.5)['x'][0]
            Betta_temp.append(_betta)

    #попробуем предварительно пробежать по веткам характеристики, откуда узнать угловой коэффициент прямой, экстраполирующей исходные данные по краяем напорной ветки. Потом построить зависимость угловойго коэффициента от обортов. И далее из этой зависимости строить экстраполирующие прямые для любой ветки.
    n_points=2
    
    low_betta=Betta_temp[0:n_points]
    low_G=G_temp[0:n_points]
    low_PR=PR_temp[0:n_points]
    low_Eff=Eff_temp[0:n_points]
    if type_of_map=="turbine":
        low_Gn=Gn_temp[0:n_points]
        if "L" in temp_data:
            low_L=L_temp[0:n_points]
        if 'A' in temp_data:
            low_A=A_temp[0:n_points]
        
    high_betta=Betta_temp[-n_points:]
    high_G=G_temp[-n_points:]
    high_PR=PR_temp[-n_points:]
    high_Eff=Eff_temp[-n_points:]
    if type_of_map=="turbine":
        high_Gn=Gn_temp[-n_points:]
        if "L" in temp_data:
            high_L=L_temp[-n_points:]
        if 'A' in temp_data:
            high_A=A_temp[-n_points:]
        
    _slope_G_low=np.polyfit(x=low_betta,y=low_G,deg=1)[0]   #NB!!! здесь стоит поиграться со степенями полинома, иногда хорошо подходит 1-2 степени
    _slope_PR_low=np.polyfit(x=low_betta,y=low_PR,deg=1)[0]
    _slope_Eff_low=np.polyfit(x=low_betta,y=low_Eff,deg=1)[0]
    _slope_G_high=np.polyfit(x=high_betta,y=high_G,deg=1)[0]
    _slope_PR_high=np.polyfit(x=high_betta,y=high_PR,deg=1)[0]
    _slope_Eff_high=np.polyfit(x=high_betta,y=high_Eff,deg=1)[0]
    if type_of_map=="turbine":
        _slope_Gn_low=np.polyfit(x=low_betta,y=low_Gn,deg=1)[0]
        _slope_Gn_high=np.polyfit(x=high_betta,y=high_Gn,deg=1)[0]
        if "L" in temp_data:
            _slope_L_low=np.polyfit(x=low_betta,y=low_L,deg=1)[0]
            _slope_L_high=np.polyfit(x=high_betta,y=high_L,deg=1)[0]
        if 'A' in temp_data:
            _slope_A_low=np.polyfit(x=low_betta,y=low_A,deg=1)[0]
            _slope_A_high=np.polyfit(x=high_betta,y=high_A,deg=1)[0]
    
    #сохранияем угловые коэффициенты в массив
    if 'slopes_G_low' not in locals():
        slopes_G_low=[]
        slopes_PR_low=[]
        slopes_Eff_low=[]
        slopes_G_high=[]
        slopes_PR_high=[]
        slopes_Eff_high=[]
        # mins_G=[]
        # maxs_G=[]
        # maxs_PR=[]
        # maxs_Eff=[]
        if type_of_map=="turbine":
            slopes_Gn_low=[]
            slopes_Gn_high=[]
            # maxs_Gn=[]
            if "L" in temp_data:
                slopes_L_low=[]
                slopes_L_high=[]
                # maxs_L=[]
            if "A" in temp_data:
                slopes_A_low=[]
                slopes_A_high=[]
                # maxs_A=[]
                
        bettas=pd.Series(dtype=float)
    slopes_G_low.append(_slope_G_low)
    slopes_PR_low.append(_slope_PR_low)
    slopes_Eff_low.append(_slope_Eff_low)
    slopes_G_high.append(_slope_G_high)
    slopes_PR_high.append(_slope_PR_high)
    slopes_Eff_high.append(_slope_Eff_high)
    # mins_G.append(min_G)
    # maxs_G.append(max_G)
    # maxs_PR.append(max_PR)
    # maxs_Eff.append(max_Eff)
    if type_of_map=="turbine":
        slopes_Gn_low.append(_slope_Gn_low)
        slopes_Gn_high.append(_slope_Gn_high)
        # maxs_Gn.append(max_Gn)
        if "L" in temp_data:
            slopes_L_low.append(_slope_L_low)
            slopes_L_high.append(_slope_L_high)
            # maxs_L.append(max_L)
        if "A" in temp_data:
            slopes_A_low.append(_slope_A_low)
            slopes_A_high.append(_slope_A_high)
            # maxs_A.append(max_A)
    _betta=pd.Series(Betta_temp)
    bettas=bettas.append(_betta,ignore_index=True)
    
    # temp_data=temp_data.assign(G=G_temp, PR=PR_temp, Eff=Eff_temp)
    temp_data['betta']=bettas
    # if type_of_map=="turbine":
    #     temp_data=temp_data.assign(Gn=Gn_temp)
    #     if "L" in temp_data:
    #         temp_data=temp_data.assign(L=L_temp)
    #     if "A" in temp_data:
    #         temp_data=temp_data.assign(A=A_temp)
    if "initial_reader" not in locals():
        initial_reader = reader.copy()
        # reader['betta']=np.nan
    reader.update(temp_data)    
    
DATA['initial_reader']=initial_reader 
    
#строим регрессию на основе значений угловых коэффициентов и значений оборотов
_rotations=np.concatenate([rotations[0]*0.9,rotations[0]*0.933,rotations[0]*0.966,rotations,rotations[-1]*1.033,rotations[-1]*1.066,rotations[-1]*1.1],axis=None)
_rotations2=np.concatenate([rotations,rotations[-1]*1.033,rotations[-1]*1.066,rotations[-1]*1.1],axis=None)


#NB!!! шесть функций ниже можно и вероятно нужно каждый раз подгонять, пока вручную:( в идеале здесь должно быть можно выбирать вид аппроксимиорующей функции: сплайн или полином, их степень, коэффициент сглаживания, д.б. возможность корректировать исходные точки. Идеально было бы все это делать в графическом виде (Tkinter?))
#если результирующая функция пересекает ноль, то скорее всего что-то не так
# slopes_G_low_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_G_low[0],slopes_G_low[0],slopes_G_low[0],slopes_G_low,slopes_G_low[-1],slopes_G_low[-1],slopes_G_low[-1]],axis=None),deg=2))
slopes_G_low_func=Akima1DInterpolatorModified(x=_rotations,y=np.concatenate([slopes_G_low[0],slopes_G_low[0],slopes_G_low[0],slopes_G_low,slopes_G_low[-1],slopes_G_low[-1],slopes_G_low[-1]],axis=None))
slopes_PR_low_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_PR_low[0],slopes_PR_low[0],slopes_PR_low[0],slopes_PR_low,slopes_PR_low[-1],slopes_PR_low[-1],slopes_PR_low[-1]],axis=None),deg=3))
slopes_Eff_low_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_Eff_low[0],slopes_Eff_low[0],slopes_Eff_low[0],slopes_Eff_low,slopes_Eff_low[-1],slopes_Eff_low[-1],slopes_Eff_low[-1]],axis=None),deg=3))
# slopes_G_high_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_G_high[0],slopes_G_high[0],slopes_G_high[0],slopes_G_high[:-4],slopes_G_high[-1]-0.017,slopes_G_high[-1]-0.017,slopes_G_high[-1]-0.017,slopes_G_high[-1]-0.017,slopes_G_high[-1]-0.017,slopes_G_high[-1]-0.017,slopes_G_high[-1]-0.017],axis=None),deg=3))
#корректируем вручную массив slopes_G_high
# slopes_G_high[2]=-10.0;slopes_G_high[3]=-1.0;slopes_G_high[4]=-0.5;slopes_G_high[5]=0.0;
# slopes_G_high = [-20.0, -10.0, -1.0, -0.5, -0.0, 0.0]
slopes_G_high[2]=-15
slopes_G_high[-1]=slopes_G_high[-1]
# slopes_G_high[3]=slopes_G_high[4]
# slopes_G_high_func=np.poly1d(np.polyfit(x=_rotations2,y=np.concatenate([slopes_G_high,slopes_G_high[-1],slopes_G_high[-1],slopes_G_high[-1]],axis=None),deg=4))
# slopes_G_high_func=UnivariateSplineModified(x=_rotations2,y=np.concatenate([slopes_G_high,slopes_G_high[-1],slopes_G_high[-1],slopes_G_high[-1]],axis=None)-0.0,k=4,s=5)
slopes_G_high_func=Akima1DInterpolatorModified(x=_rotations2,y=np.concatenate([slopes_G_high,slopes_G_high[-1],slopes_G_high[-1],slopes_G_high[-1]],axis=None))
slopes_PR_high_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_PR_high[0],slopes_PR_high[0],slopes_PR_high[0],slopes_PR_high,slopes_PR_high[-1],slopes_PR_high[-1],slopes_PR_high[-1]],axis=None),deg=3))
slopes_Eff_high_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_Eff_high[0],slopes_Eff_high[0],slopes_Eff_high[0],slopes_Eff_high,slopes_Eff_high[-1],slopes_Eff_high[-1],slopes_Eff_high[-1]],axis=None),deg=3))
# slopes_Eff_high_func=np.poly1d(np.polyfit(x=_rotations,y=np.concatenate([slopes_Eff_high[1],slopes_Eff_high[1],slopes_Eff_high[1],slopes_Eff_high[1],slopes_Eff_high[1:-1],slopes_Eff_high[-2],slopes_Eff_high[-2],slopes_Eff_high[-2],slopes_Eff_high[-2]],axis=None),deg=3))
if type_of_map=="turbine":
    slopes_Gn_low_func=np.poly1d(np.polyfit(x=rotations,y=slopes_Gn_low,deg=3))
    slopes_Gn_high_func=np.poly1d(np.polyfit(x=rotations,y=slopes_Gn_high,deg=3))
    if "L" in temp_data:
        slopes_L_low_func=np.poly1d(np.polyfit(x=rotations,y=slopes_L_low,deg=3))
        slopes_L_high_func=np.poly1d(np.polyfit(x=rotations,y=slopes_L_high,deg=3))
    if "A" in temp_data:
        slopes_A_low_func=np.poly1d(np.polyfit(x=rotations,y=slopes_A_low,deg=3))
        slopes_A_high_func=np.poly1d(np.polyfit(x=rotations,y=slopes_A_high,deg=3))

# проверяем графиками углвые коэффициенты: точками углвые коэффициенты, и линией - регрессию
if type_of_map=="compressor":
    _rotations=np.linspace(rotations[0]*0.9,rotations[-1]*1.1,200)
    _slopes_G_low=[slopes_G_low_func(n) for n in _rotations]
    _slopes_G_high=[slopes_G_high_func(n) for n in _rotations]
    _slopes_PR_low=[slopes_PR_low_func(n) for n in _rotations]
    _slopes_PR_high=[slopes_PR_high_func(n) for n in _rotations]
    _slopes_Eff_low=[slopes_Eff_low_func(n) for n in _rotations]
    _slopes_Eff_high=[slopes_Eff_high_func(n) for n in _rotations]
    
    points_for_scatter=[{'x':rotations,'y':slopes_G_low,'label':'slopes_G_low'},
                        {'x':rotations,'y':slopes_G_high,'label':'slopes_G_high'},
                        {'x':rotations,'y':slopes_PR_low,'label':'slopes_PR_low'},
                        {'x':rotations,'y':slopes_PR_high,'label':'slopes_PR_high'},
                        {'x':rotations,'y':slopes_Eff_low,'label':'slopes_Eff_low'},
                        {'x':rotations,'y':slopes_Eff_high,'label':'slopes_Eff_high'}]
    points_for_plot=[{'x':_rotations,'y':_slopes_G_low,'label':'slopes_G_low'},
                        {'x':_rotations,'y':_slopes_G_high,'label':'slopes_G_high'},
                        {'x':_rotations,'y':_slopes_PR_low,'label':'slopes_PR_low'},
                        {'x':_rotations,'y':_slopes_PR_high,'label':'slopes_PR_high'},
                        {'x':_rotations,'y':_slopes_Eff_low,'label':'slopes_Eff_low'},
                        {'x':_rotations,'y':_slopes_Eff_high,'label':'slopes_Eff_high'}]
    _fig.add_chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,title='Коэффициенты k (slope) линейного уравнения y=k*x+b для разных оборотов и соответствующая регрессия',xlabel='n',ylabel='slope',ylim=[-100,10])

if type_of_map=="turbine":       
    _rotations=np.linspace(rotations[0]*0.9,rotations[-1]*1.1,200)
    _slopes_G_low=[slopes_G_low_func(n) for n in _rotations]
    _slopes_G_high=[slopes_G_high_func(n) for n in _rotations]
    _slopes_Gn_low=[slopes_Gn_low_func(n) for n in _rotations]
    _slopes_Gn_high=[slopes_Gn_high_func(n) for n in _rotations]
    _slopes_PR_low=[slopes_PR_low_func(n) for n in _rotations]
    _slopes_PR_high=[slopes_PR_high_func(n) for n in _rotations]
    _slopes_Eff_low=[slopes_Eff_low_func(n) for n in _rotations]
    _slopes_Eff_high=[slopes_Eff_high_func(n) for n in _rotations]
    
    points_for_scatter=[{'x':rotations,'y':slopes_G_low,'label':'slopes_G_low'},
                        {'x':rotations,'y':slopes_G_high,'label':'slopes_G_high'},
                        {'x':rotations,'y':slopes_Gn_low,'label':'slopes_Gn_low'},
                        {'x':rotations,'y':slopes_Gn_high,'label':'slopes_Gn_high'},
                        {'x':rotations,'y':slopes_PR_low,'label':'slopes_PR_low'},
                        {'x':rotations,'y':slopes_PR_high,'label':'slopes_PR_high'},]
    points_for_scatter_Eff=[{'x':rotations,'y':slopes_Eff_low,'label':'slopes_Eff_low'},
                        {'x':rotations,'y':slopes_Eff_high,'label':'slopes_Eff_high'}]
    points_for_plot=[{'x':_rotations,'y':_slopes_G_low,'label':'slopes_G_low'},
                        {'x':_rotations,'y':_slopes_G_high,'label':'slopes_G_high'},
                        {'x':_rotations,'y':_slopes_Gn_low,'label':'slopes_Gn_low'},
                        {'x':_rotations,'y':_slopes_Gn_high,'label':'slopes_Gn_high'},
                        {'x':_rotations,'y':_slopes_PR_low,'label':'slopes_PR_low'},
                        {'x':_rotations,'y':_slopes_PR_high,'label':'slopes_PR_high'},]
    points_for_plot_Eff=[{'x':_rotations,'y':_slopes_Eff_low,'label':'slopes_Eff_low'},
                        {'x':_rotations,'y':_slopes_Eff_high,'label':'slopes_Eff_high'}]
    chart.Chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,title='Коэффициенты k (slope) линейного уравнения y=k*x+b для разных оборотов и соответствующая регрессия',xlabel='n',ylabel='slope')
    chart.Chart(points_for_scatter=points_for_scatter_Eff,points_for_plot=points_for_plot_Eff,title='Коэффициенты k (slope) линейного уравнения y=k*x+b для разных оборотов и соответствующая регрессия',xlabel='n',ylabel='slope')

#проходимся по всем заданным веткам оборотов, достраиваем несколько точек для экстраполяции на основе полученных выше угловых коэффициентов slopes. экстраполируем используя для каждой ветки оборотов максимально (или минимальное) значение бетта и прибавляя к нему (или вычитая из него) значение 0.1, 0.2 и 0.3 - т.е. экстраполируем на 3 точки
rel_minimums={'G':[],'PR':[],'Eff':[],'Gn':[],'A':[],'L':[]}
rel_maximums={'G':[],'PR':[],'Eff':[],'Gn':[],'A':[],'L':[]}
for ni in rotations:
    temp_data=reader.loc[reader.n == ni] #выделяем из общего массива данных только те, что относятся к определенным оборотам nx
    G_temp=temp_data.G
    Eff_temp=temp_data.Eff
    PR_temp=temp_data.PR
    betta_temp=temp_data.betta
    if type_of_map=="turbine":
        Gn_temp=temp_data.Gn
        if "L" in temp_data:
            L_temp=temp_data.L
        if 'A' in temp_data:
            A_temp=temp_data.A

    slope_G_low=slopes_G_low_func(ni)
    slope_PR_low=slopes_PR_low_func(ni)
    slope_Eff_low=slopes_Eff_low_func(ni)
    slope_G_high=slopes_G_high_func(ni)
    slope_PR_high=slopes_PR_high_func(ni)
    slope_Eff_high=slopes_Eff_high_func(ni)
    intercept_G_low=G_temp.iloc[0]-slope_G_low*betta_temp.iloc[0]
    intercept_PR_low=PR_temp.iloc[0]-slope_PR_low*betta_temp.iloc[0]
    intercept_Eff_low=Eff_temp.iloc[0]-slope_Eff_low*betta_temp.iloc[0]
    intercept_G_high=G_temp.iloc[-1]-slope_G_high*betta_temp.iloc[-1]
    intercept_PR_high=PR_temp.iloc[-1]-slope_PR_high*betta_temp.iloc[-1]
    intercept_Eff_high=Eff_temp.iloc[-1]-slope_Eff_high*betta_temp.iloc[-1]
    if type_of_map=="turbine":
        slope_Gn_low=slopes_Gn_low_func(ni)
        slope_Gn_high=slopes_Gn_high_func(ni)
        intercept_Gn_low=Gn_temp.iloc[0]-slope_Gn_low*betta_temp.iloc[0]
        intercept_Gn_high=Gn_temp.iloc[-1]-slope_Gn_high*betta_temp.iloc[-1]
        if "L" in temp_data:
            slope_L_low=slopes_L_low_func(ni)
            slope_L_high=slopes_L_high_func(ni)
            intercept_L_low=L_temp.iloc[0]-slope_L_low*betta_temp.iloc[0]
            intercept_L_high=L_temp.iloc[-1]-slope_L_high*betta_temp.iloc[-1]
        if "A" in temp_data:
            slope_A_low=slopes_A_low_func(ni)
            slope_A_high=slopes_A_high_func(ni)
            intercept_A_low=A_temp.iloc[0]-slope_A_low*betta_temp.iloc[0]
            intercept_A_high=A_temp.iloc[-1]-slope_A_high*betta_temp.iloc[-1]
   
    low_extr_func_G=np.poly1d([slope_G_low,intercept_G_low])
    low_extr_func_PR=np.poly1d([slope_PR_low,intercept_PR_low])
    low_extr_func_Eff=np.poly1d([slope_Eff_low,intercept_Eff_low])
    high_extr_func_G=np.poly1d([slope_G_high,intercept_G_high])
    high_extr_func_PR=np.poly1d([slope_PR_high,intercept_PR_high])
    high_extr_func_Eff=np.poly1d([slope_Eff_high,intercept_Eff_high])
    if type_of_map=="turbine":
        low_extr_func_Gn=np.poly1d([slope_Gn_low,intercept_Gn_low])
        high_extr_func_Gn=np.poly1d([slope_Gn_high,intercept_Gn_high])
        if "L" in temp_data:
            low_extr_func_L=np.poly1d([slope_L_low,intercept_L_low])
            high_extr_func_L=np.poly1d([slope_L_high,intercept_L_high])
        if "A" in temp_data:
            low_extr_func_A=np.poly1d([slope_A_low,intercept_A_low])
            high_extr_func_A=np.poly1d([slope_A_high,intercept_A_high])
            
        
    min_betta=betta_temp.iloc[0]
    max_betta=betta_temp.iloc[-1]
    if max_betta < min_betta:
        print('Ошибка в определении максимального и минимального значений бетта!')
    low_betta_extrapolate=pd.Series([min_betta-0.3,min_betta-0.2,min_betta-0.1])
    high_betta_extrapolate=pd.Series([max_betta+0.1,max_betta+0.2,max_betta+0.3])
    low_G_extrapolate=pd.Series([low_extr_func_G(val) for val in low_betta_extrapolate])
    low_PR_extrapolate=pd.Series([low_extr_func_PR(val) for val in low_betta_extrapolate])
    low_Eff_extrapolate=pd.Series([low_extr_func_Eff(val) for val in low_betta_extrapolate])
    high_G_extrapolate=pd.Series([high_extr_func_G(val) for val in high_betta_extrapolate])
    high_PR_extrapolate=pd.Series([high_extr_func_PR(val) for val in high_betta_extrapolate])
    high_Eff_extrapolate=pd.Series([high_extr_func_Eff(val) for val in high_betta_extrapolate])
    if type_of_map=="turbine":
        low_Gn_extrapolate=pd.Series([low_extr_func_Gn(val) for val in low_betta_extrapolate])
        high_Gn_extrapolate=pd.Series([high_extr_func_Gn(val) for val in high_betta_extrapolate])
        if "L" in temp_data:
            low_L_extrapolate=pd.Series([low_extr_func_L(val) for val in low_betta_extrapolate])
            high_L_extrapolate=pd.Series([high_extr_func_L(val) for val in high_betta_extrapolate])            
        if "A" in temp_data:
            low_A_extrapolate=pd.Series([low_extr_func_A(val) for val in low_betta_extrapolate])
            high_A_extrapolate=pd.Series([high_extr_func_A(val) for val in high_betta_extrapolate])   
    _G= pd.concat([low_G_extrapolate,G_temp,high_G_extrapolate],ignore_index=True)
    _PR= pd.concat([low_PR_extrapolate,PR_temp,high_PR_extrapolate],ignore_index=True)
    _Eff= pd.concat([low_Eff_extrapolate,Eff_temp,high_Eff_extrapolate],ignore_index=True)
    _betta= pd.concat([low_betta_extrapolate,pd.Series(betta_temp),high_betta_extrapolate],ignore_index=True)
    if type_of_map=="turbine":
        _Gn= pd.concat([low_Gn_extrapolate,Gn_temp,high_Gn_extrapolate],ignore_index=True)
        if "L" in temp_data:
            _L= pd.concat([low_L_extrapolate,L_temp,high_L_extrapolate],ignore_index=True)
        if "A" in temp_data:
            _A= pd.concat([low_A_extrapolate,A_temp,high_A_extrapolate],ignore_index=True)
    #далее экстраполировав имеющиеся данные приведем их к относительному виду, т.к. таким образом в дальнейшем гораздо удобнее и корректнее делать аппроксимацию полиномами (иначе аппроксимации могут быть кривыми)
    min_G=_G.min()  
    max_G=(_G-min_G).max()
    rel_minimums['G'].append(min_G)
    rel_maximums['G'].append(max_G)
    _G_rel=(_G-min_G)/max_G #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются

    min_PR=_PR.min()  
    max_PR=(_PR-min_PR).max()
    rel_minimums['PR'].append(min_PR)
    rel_maximums['PR'].append(max_PR)
    _PR_rel=(_PR-min_PR)/max_PR #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются

    min_Eff=_Eff.min()  
    max_Eff=(_Eff-min_Eff).max()
    rel_minimums['Eff'].append(min_Eff)
    rel_maximums['Eff'].append(max_Eff)
    _Eff_rel=(_Eff-min_Eff)/max_Eff #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются

    if type_of_map=="turbine":
        min_Gn=_Gn.min()  
        max_Gn=(_Gn-min_Gn).max()
        rel_minimums['Gn'].append(min_Gn)
        rel_maximums['Gn'].append(max_Gn)
        _Gn_rel=(_Gn-min_Gn)/max_Gn #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются
        
        if "L" in temp_data:
            min_L=_L.min()  
            max_L=(_L-min_L).max()
            rel_minimums['L'].append(min_L)
            rel_maximums['L'].append(max_L)
            _L_rel=(_L-min_L)/max_L #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются

        if "A" in temp_data:
            min_A=_A.min()  
            max_A=(_A-min_A).max()
            rel_minimums['A'].append(min_A)
            rel_maximums['A'].append(max_A)
            _A_rel=(_A-min_A)/max_A #с помощью деления всего массива на его же максимальное значение мы приводим значения к относительному виду, как показывает практика это влияет на вид аппроксимирующей функции - без нормализации функция может выглядеть криво, особенно если порядки величин X и Y сильно отличаются

    if type_of_map=="compressor":    
        _temp=pd.concat([_G,_PR,_Eff,_betta,_G_rel,_PR_rel,_Eff_rel],axis=1,keys=['G','PR','Eff','betta','G_rel','PR_rel','Eff_rel'])
    elif type_of_map=="turbine":
        _temp=pd.concat([_G,_Gn,_PR,_Eff,_betta,_G_rel,_Gn,_PR_rel,_Eff_rel],axis=1,keys=['G','Gn','PR','Eff','betta','G_rel','Gn_rel','PR_rel','Eff_rel'])
        if "L" in temp_data:
            _temp['L_rel']=_L_rel
            # _temp=pd.concat([_temp,_L],axis=1,keys=['L'])
        if "A" in temp_data:
            _temp['A_rel']=_A_rel
            # _temp=pd.concat([_temp,_A],axis=1,keys=['A'])
    _temp['n']=ni
    #обновим массив reader новыми данными создав идентичный массив new_reader
    if 'new_reader' not in locals():
        new_reader=pd.DataFrame(_temp)
    else:
        new_reader=new_reader.append(_temp,ignore_index=True)

DATA['new_reader']=new_reader
DATA['rel_maximums']=rel_maximums
DATA['rel_minimums']=rel_minimums
# reader=new_reader  #обновляем массив reader с учетом добавленных экстраполируемых точек

G_output=[]
Eff_output=[]
PR_output=[] 
if type_of_map=="turbine":
    Gn_output=[] #для турбины
    L_output=[] #для турбины
    A_output=[] #для турбины
    
quantity_of_rotations=len(rotations)#для этого сначала надо знать количество напорных веток    
cmap = plt.get_cmap('jet') #используем палитру jet из матплотлиба
colors = [cmap(i) for i in np.linspace(0, 1, quantity_of_rotations)]

scatter_GPR=[]
plot_GPR=[]
scatter_GEff=[]
plot_GEff=[]
scatter_PREff=[]
plot_PREff=[]
scatter_BettaPR=[]
plot_BettaPR=[]
scatter_BettaG=[]
plot_BettaG=[]
scatter_BettaGn=[]
plot_BettaGn=[]
scatter_BettaEff=[]
plot_BettaEff=[]
if type_of_map=="turbine":
    scatter_GnPR=[]
    plot_GnPR=[]
    scatter_GnEff=[]
    plot_GnEff=[]
    scatter_APR=[]
    plot_APR=[]
    scatter_LPR=[]
    plot_LPR=[]

for ind,ni_color in enumerate(zip(rotations,colors)):#проходимся по всем заданным веткам оборотов, строим графики для проверки
    ni=ni_color[0]
    color=ni_color[1]
    temp_data=new_reader.loc[new_reader.n == ni] #выделяем из общего массива данных только те, что относятся к определенным оборотам nx
    # temp_data2=initial_reader.loc[initial_reader.n == ni]
    G_temp=temp_data.G_rel
    Eff_temp=temp_data.Eff_rel
    PR_temp=temp_data.PR_rel
    G_temp_abs=temp_data.G
    Eff_temp_abs=temp_data.Eff
    PR_temp_abs=temp_data.PR
    Betta_temp=temp_data.betta
    max_Eff=max(Eff_temp)
    if type_of_map=="turbine":
        Gn_temp=temp_data.Gn_rel
        A_temp=temp_data.A_rel
        L_temp=temp_data.L_rel
    
    #формируем словари для отрисоквки графиков после завершения цикла
    _scatter_GPR={'x':G_temp,'y':PR_temp,'label':ni,'c':color}
    _plot_GPR={'x':G_temp,'y':PR_temp,'c':color}
    _scatter_GEff={'x':G_temp,'y':Eff_temp,'label':ni,'c':color}
    _plot_GEff={'x':G_temp,'y':Eff_temp,'c':color}
    _scatter_PREff={'x':PR_temp,'y':Eff_temp,'label':ni,'c':color}
    _plot_PREff={'x':PR_temp,'y':Eff_temp,'c':color}
    _scatter_BettaPR={'x':Betta_temp,'y':PR_temp,'label':ni,'c':color}
    _plot_BettaPR={'x':Betta_temp,'y':PR_temp,'c':color}
    _scatter_BettaG={'x':Betta_temp,'y':G_temp,'label':ni,'c':color}
    _plot_BettaG={'x':Betta_temp,'y':G_temp,'c':color}
    _scatter_BettaEff={'x':Betta_temp,'y':Eff_temp,'label':ni,'c':color}
    _plot_BettaEff={'x':Betta_temp,'y':Eff_temp,'c':color}
    if type_of_map=="turbine":
        _scatter_GnPR={'y':Gn_temp,'x':PR_temp,'label':ni,'c':color}
        _plot_GnPR={'y':Gn_temp,'x':PR_temp,'c':color}
        _scatter_GnEff={'x':Gn_temp,'y':Eff_temp,'label':ni,'c':color}
        _plot_GnEff={'x':Gn_temp,'y':Eff_temp,'c':color}
        _scatter_APR={'y':A_temp,'x':PR_temp,'label':ni,'c':color}
        _plot_APR={'y':A_temp,'x':PR_temp,'c':color}
        _scatter_LPR={'y':L_temp,'x':PR_temp,'label':ni,'c':color}
        _plot_LPR={'y':L_temp,'x':PR_temp,'c':color}
        _scatter_BettaGn={'x':Betta_temp,'y':Gn_temp,'label':ni,'c':color}
        _plot_BettaGn={'x':Betta_temp,'y':Gn_temp,'c':color}
    
    scatter_GPR.append(_scatter_GPR)
    plot_GPR.append(_plot_GPR)
    scatter_GEff.append(_scatter_GEff)
    plot_GEff.append(_plot_GEff)
    scatter_PREff.append(_scatter_PREff)
    plot_PREff.append(_plot_PREff)
    scatter_BettaPR.append(_scatter_BettaPR)
    plot_BettaPR.append(_plot_BettaPR)
    scatter_BettaG.append(_scatter_BettaG)
    plot_BettaG.append(_plot_BettaG)
    scatter_BettaEff.append(_scatter_BettaEff)
    plot_BettaEff.append(_plot_BettaEff)
    if type_of_map=="turbine":
        scatter_GnPR.append(_scatter_GnPR)
        plot_GnPR.append(_plot_GnPR)
        scatter_GnEff.append(_scatter_GnEff)
        plot_GnEff.append(_plot_GnEff)
        scatter_APR.append(_scatter_APR)
        plot_APR.append(_plot_APR)
        scatter_LPR.append(_scatter_LPR)
        plot_LPR.append(_plot_LPR)
        scatter_BettaGn.append(_scatter_BettaGn)
        plot_BettaGn.append(_plot_BettaGn)
    
    #аппроксимируем функцию и вторую производную на основе исходных точек
    G_func_rel=UnivariateSplineModified(Betta_temp,G_temp,k=5,s=0.0001)#!!! Здесь нужно правильно выбрать аппроксимирующую функцию, точная сплайн-интерполяция хороша только если исходные данные обладают высокой точностью, иначе лучше использовать аппроксимацию
    G_func_rel_der2=G_func_rel.derivative(2)
    G_func=f_factory(G_func_rel,rel_maximums['G'].pop(0),rel_minimums['G'].pop(0))

    Eff_func_rel=UnivariateSplineModified(Betta_temp,Eff_temp,k=4,s=0.0005)#!!! Здесь нужно правильно выбрать аппроксимирующую функцию, точная сплайн-интерполяция хороша только если исходные данные обладают высокой точностью, иначе лучше использовать аппроксимацию
    Eff_func_rel_der2=Eff_func_rel.derivative(2)
    Eff_func=f_factory(Eff_func_rel,rel_maximums['Eff'].pop(0),rel_minimums['Eff'].pop(0))

    PR_func_rel=UnivariateSplineModified(Betta_temp,PR_temp,k=5,s=0.0001)#!!! Здесь нужно правильно выбрать аппроксимирующую функцию, точная сплайн-интерполяция хороша только если исходные данные обладают высокой точностью, иначе лучше использовать аппроксимацию
    PR_func_rel_der2=PR_func_rel.derivative(2)
    PR_func=f_factory(PR_func_rel,rel_maximums['PR'].pop(0),rel_minimums['PR'].pop(0))

    if type_of_map=="turbine":
#        L_func=Akima1DInterpolatorModified(Betta_temp,L_temp)
#        A_func=Akima1DInterpolatorModified(Betta_temp,A_temp)
        if 'Gn_temp' in globals():
            Gn_func_rel=UnivariateSplineModified(Betta_temp,Gn_temp.tolist(),k=5,s=0.001)
            Gn_func_rel_der2=Gn_func_rel.derivative(2)
            Gn_func=f_factory(Gn_func_rel,rel_maximums['Gn'].pop(0),rel_minimums['Gn'].pop(0))
        if 'L_temp' in globals():
            L_func_rel=UnivariateSplineModified(Betta_temp,L_temp.tolist(),k=5,s=0.0001)
            L_func_rel_der2=L_func_rel.derivative(2)
            L_func=f_factory(L_func_rel,rel_maximums['L'].pop(0),rel_minimums['L'].pop(0))
            # def L_func(x):
            #     return L_func_rel(x)*max_L
        if 'A_temp' in globals():
            A_func_rel=UnivariateSplineModified(Betta_temp,A_temp.tolist(),k=5,s=0.001)
            A_func_rel_der2=A_func_rel.derivative(2)
            A_func=f_factory(A_func_rel,rel_maximums['A'].pop(0),rel_minimums['A'].pop(0))
            # def A_func(x):
            #     return A_func_rel(x)*max_A
    G_output.append(G_func) #сохраняем в список ссылки на функции интерполяции параметра от бетта для каждой ветки оборотов
    PR_output.append(PR_func)
    Eff_output.append(Eff_func)
    if type_of_map=="turbine":
        if 'Gn_func_rel' in globals():
            Gn_output.append(Gn_func)
        if 'L_func_rel' in globals():
            L_output.append(L_func)
        if 'A_func_rel' in globals():
            A_output.append(A_func)
            
#4.2) проверяем поветочно. Т.е. строим графики исходных данных (обозначены точками) и обработанных кривых отдельно для каждой ветки оборотов
    bbb=np.linspace(-0.5,1.5,200)
    GGG=[]
    PRRR=[]
    Efff=[]
    GGG2=[]
    PRRR2=[]
    Efff2=[]
    GGG_der2=[]
    PRRR_der2=[]
    Efff_der2=[]
    if type_of_map=="turbine":
        GGGn=[]
        LLL=[]
        AAA=[]
        GGGn_der2=[]
        AAA_der2=[]
        LLL_der2=[]
    for betta_i in bbb:
        GGG.append(float(G_func_rel(betta_i)))
        GGG2.append(float(G_func(betta_i)))
        GGG_der2.append(float(G_func_rel_der2(betta_i)))
        PRRR.append(float(PR_func_rel(betta_i)))
        PRRR2.append(float(PR_func(betta_i)))
        PRRR_der2.append(float(PR_func_rel_der2(betta_i)))
        Efff.append(float(Eff_func_rel(betta_i)))
        Efff2.append(float(Eff_func(betta_i)))
        Efff_der2.append(float(Eff_func_rel_der2(betta_i)))
        if type_of_map=="turbine":
            if 'Gn_func_rel' in globals():
                GGGn.append(float(Gn_func_rel(betta_i)))
                GGGn_der2.append(float(Gn_func_rel_der2(betta_i)))
            if 'L_func_rel' in globals():
                LLL.append(float(L_func_rel(betta_i)))
                LLL_der2.append(float(L_func_rel_der2(betta_i)))
            if 'A_func_rel' in globals():
                AAA.append(float(A_func_rel(betta_i)))
                AAA_der2.append(float(A_func_rel_der2(betta_i)))
            
    # if type_of_map=="turbine":
    #     fig3, axes3 = plt.subplots(3,1)
    #     fig3.set_size_inches(17, 20)
    # if type_of_map=="compressor":
    #     fig3, axes3 = plt.subplots(4,1)
    #     fig3.set_size_inches(17, 24)
    
    if type_of_map=="compressor":
        points_for_scatter=[{'x':Betta_temp,'y':G_temp,'label':'G rel','c':'green'},
                            {'x':Betta_temp,'y':PR_temp,'label':'PR rel','c':'red'},
                            {'x':Betta_temp,'y':Eff_temp,'label':'Eff rel','c':'blue'}]
        
        points_for_plot=[{'x':bbb,'y':GGG,'label':'G rel','c':'green'},
                         {'x':bbb,'y':PRRR,'label':'PR rel','c':'red'},
                         {'x':bbb,'y':Efff,'label':'Eff rel','c':'blue'},
                         {'x':bbb,'y2':GGG_der2,'label':'G_curvature','c':'green','ls':':'},
                         {'x':bbb,'y2':PRRR_der2,'label':'PR_curvature','c':'red','ls':':'}]
        _fig2=chart.Chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,title='{} {}'.format('G/PR/Eff rel = f(betta). Ветка n=',ni),xlabel='betta',dpi=150,figure_size=(14,21))
        _fig2.add_chart(points_for_scatter=[{'y':PR_temp,'x':G_temp}],points_for_plot=[{'y':PRRR,'x':GGG}],title='PR rel=f(G rel). {} {}'.format('ветка n=',ni),xlabel='G rel',ylabel='PR rel')
        _fig2.add_chart(points_for_scatter=[{'y':Eff_temp,'x':G_temp}],points_for_plot=[{'y':Efff,'x':GGG}],title='Eff rel=f(G rel). {} {}'.format('ветка n=',ni),xlabel='G rel',ylabel='Eff rel')
        _fig2.add_chart(points_for_scatter=[{'y':Eff_temp,'x':PR_temp}],points_for_plot=[{'y':Efff,'x':PRRR}],title='Eff rel=f(PR rel). {} {}'.format('ветка n=',ni),xlabel='PR rel',ylabel='Eff rel',ylim=[0.2,max_Eff*1.1])
        _fig2.figure.savefig("test.jpg")
#то же самое в абс координатах
        points_for_scatter2=[{'x':Betta_temp,'y':G_temp_abs,'label':'G','c':'green'},
                            {'x':Betta_temp,'y':PR_temp_abs,'label':'PR','c':'red'},
                            {'x':Betta_temp,'y':Eff_temp_abs,'label':'Eff','c':'blue'}]
        
        points_for_plot2=[{'x':bbb,'y':GGG2,'label':'G','c':'green'},
                         {'x':bbb,'y':PRRR2,'label':'PR','c':'red'},
                         {'x':bbb,'y':Efff2,'label':'Eff','c':'blue'}]
        _fig20=chart.Chart(points_for_scatter=points_for_scatter2,points_for_plot=points_for_plot2,title='{} {}'.format('G/PR/Eff = f(betta). Ветка n=',ni),xlabel='betta',dpi=150,figure_size=(14,21))
        _fig20.add_chart(points_for_scatter=[{'y':PR_temp_abs,'x':G_temp_abs}],points_for_plot=[{'y':PRRR2,'x':GGG2}],title='PR=f(G). {} {}'.format('ветка n=',ni),xlabel='G',ylabel='PR',xlim=[0,DATA['abs_scales']['G']*1.05],ylim=[1,DATA['abs_scales']['PR']*1.1])
        _fig20.add_chart(points_for_scatter=[{'y':Eff_temp_abs,'x':G_temp_abs}],points_for_plot=[{'y':Efff2,'x':GGG2}],title='Eff=f(G). {} {}'.format('ветка n=',ni),xlabel='G',ylabel='Eff',xlim=[0,DATA['abs_scales']['G']*1.05],ylim=[0,DATA['abs_scales']['Eff']*1.05])
        _fig20.add_chart(points_for_scatter=[{'y':Eff_temp_abs,'x':PR_temp_abs}],points_for_plot=[{'y':Efff2,'x':PRRR2}],title='Eff=f(PR). {} {}'.format('ветка n=',ni),xlabel='PR',ylabel='Eff',xlim=[1,DATA['abs_scales']['PR']*1.05],ylim=[0,DATA['abs_scales']['Eff']*1.05])




    
    if type_of_map=="turbine":
        points_for_scatter=[{'x':Betta_temp,'y':Gn_temp,'label':'Gn','c':'green'},
                            {'x':Betta_temp,'y':PR_temp,'label':'PR','c':'red'},
                            {'x':Betta_temp,'y':Eff_temp,'label':'Eff','c':'blue'},
                            {'x':Betta_temp,'y':A_temp,'label':'A','c':'black'},
                            {'x':Betta_temp,'y':L_temp,'label':'L','c':'darkorange'}]
        points_for_plot=[{'x':bbb,'y':GGGn,'label':'Gn','c':'green'},
                         {'x':bbb,'y':PRRR,'label':'PR','c':'red'},
                         {'x':bbb,'y':Efff,'label':'Eff','c':'blue'},
                         {'x':bbb,'y':AAA,'label':'A','c':'black'},
                         {'x':bbb,'y':LLL,'label':'L','c':'darkorange'},
                         {'x':bbb,'y2':GGGn_der2,'label':'G_curvature','c':'green','ls':':'},
                         {'x':bbb,'y2':PRRR_der2,'label':'PR_curvature','c':'red','ls':':'}]
        _fig2=chart.Chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,title='{} {}'.format('Gn/PR/Eff rel = f(betta). Ветка n=',ni),xlabel='betta',ylabel='Gn/PR/Eff rel',dpi=150,figure_size=(14,21))
        
        points_for_scatter=[{'x':PR_temp,'y':Gn_temp,'label':'Gn=f(PR)','c':'green'},
                            {'y':Eff_temp,'x':Gn_temp,'label':'Eff=f(Gn)','c':'red'},
                            {'y':Eff_temp,'x':PR_temp,'label':'Eff=f(PR)','c':'blue'},
                            {'x':PR_temp,'y':A_temp,'label':'A=f(PR)','c':'black'},
                            {'x':PR_temp,'y':L_temp,'label':'L=f(PR)','c':'darkorange'}]
        points_for_plot=[{'x':PRRR,'y':GGGn,'label':'Gn=f(PR)','c':'green'},
                            {'y':Efff,'x':GGGn,'label':'Eff=f(Gn)','c':'red'},
                            {'y':Efff,'x':PRRR,'label':'Eff=f(PR)','c':'blue'},
                            {'x':PRRR,'y':AAA,'label':'A=f(PR)','c':'black'},
                            {'x':PRRR,'y':LLL,'label':'L=f(PR)','c':'darkorange'}]
        _fig2.add_chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,title='Gn/Eff/A/L rel. {} {}'.format('ветка n=',ni),xlabel='Gn/Eff/A/L rel',ylabel='PR/Gn rel')
        # _fig2.add_chart(points_for_scatter=[{'y':Eff_temp,'x':Gn_temp}],points_for_plot=[{'y':Efff,'x':GGGn}],title='Eff=f(Gn). {} {}'.format('ветка n=',ni),xlabel='Gn',ylabel='Eff')
        # _fig2.add_chart(points_for_scatter=[{'y':Eff_temp,'x':PR_temp}],points_for_plot=[{'y':Efff,'x':PRRR}],title='Eff=f(PR). {} {}'.format('ветка n=',ni),xlabel='PR',ylabel='Eff',ylim=[0.2,max_Eff*1.1])

if type_of_map=="compressor":
    chart.Chart(points_for_scatter=scatter_GPR,points_for_plot=plot_GPR,title='G=f(PR)',xlabel='G',ylabel='PR',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_GEff,points_for_plot=plot_GEff,title='Eff=f(G)',xlabel='G',ylabel='Eff',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_PREff,points_for_plot=plot_PREff,title='Eff=f(PR)',xlabel='PR',ylabel='Eff',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_BettaPR,points_for_plot=plot_BettaPR,title='PR=f(Betta)',xlabel='Betta',ylabel='PR',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_BettaG,points_for_plot=plot_BettaG,title='G=f(Betta) для компрессора или G*n=f(Betta) для турбины.',xlabel='Betta',ylabel='G или G*n',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_BettaEff,points_for_plot=plot_BettaEff,title='Eff=f(Betta)',xlabel='Betta',ylabel='Eff',dpi=150,figure_size=(14,7))
if type_of_map=="turbine": 
    chart.Chart(points_for_scatter=scatter_GnPR,points_for_plot=plot_GnPR,title='G*n=f(PR) rel.',xlabel='PR',ylabel='Gn',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_GEff,points_for_plot=plot_GEff,title='Eff=f(G*n) rel.',xlabel='Gn',ylabel='Eff',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_PREff,points_for_plot=plot_PREff,title='Eff=f(PR) rel',xlabel='PR',ylabel='Eff',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_BettaPR,points_for_plot=plot_BettaPR,title='PR=f(Betta) rel',xlabel='Betta',ylabel='PR',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_BettaG,points_for_plot=plot_BettaG,title='G*n=f(Betta) rel',xlabel='Betta',ylabel='Gn',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_BettaEff,points_for_plot=plot_BettaEff,title='Eff=f(Betta) rel',xlabel='Betta',ylabel='Eff',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_APR,points_for_plot=plot_APR,title='A=f(PR) rel',xlabel='PR',ylabel='A',dpi=150,figure_size=(14,7))
    chart.Chart(points_for_scatter=scatter_LPR,points_for_plot=plot_LPR,title='L=f(PR) rel',xlabel='PR',ylabel='L',dpi=150,figure_size=(14,7))


#5) Формируем результирующую функцию поиска нужных параметров по значению оборотов n и вспомогательного параметра betta
def Parameters_out(betta,n): 
    G_vector=[]
    PR_vector=[]
    Eff_vector=[]
    
    if type_of_map=="turbine":
        Gn_vector=[]
        A_vector=[]
        L_vector=[]  
    
    for ind, n_i in enumerate(rotations):
        G_vector.append(G_output[ind](betta)) #здесь ind - порядковый номер ветки оборотов,G_output[ind] - функция, где храняится интерполирующая функция параметра от бетта, в нее мы передаем бетта и находим значение параметра
        PR_vector.append(PR_output[ind](betta))
        Eff_vector.append(Eff_output[ind](betta))
        if type_of_map=="turbine":
            if len(Gn_output)>0:   
                Gn_vector.append(Gn_output[ind](betta))
            if len(A_output)>0:   
                A_vector.append(A_output[ind](betta))
            if len(L_output)>0:
                L_vector.append(L_output[ind](betta))
    s_for_G=interp1d([-1,0,1,2],[0.00001,0.0000005,0.0000005,0.00001],fill_value=(1,1))
    s_for_PR=interp1d([-1,0,1,2],[0.0001,0.00000005,0.00000005,0.0001],fill_value=(1,1))
    s_for_Eff=interp1d([-1,0,0.85,0.9,2],[0.0001,0.000005,0.000005,0.0001,0.0005],fill_value=(1,1))
    max_G=max(G_vector)
    max_PR=max(PR_vector)
    max_Eff=max(Eff_vector)
    if type_of_map=="turbine":
        s_for_Gn=interp1d([-1,0,1,2],[0.001,0.0001,0.0001,0.001],fill_value=(1,1))
        s_for_A=interp1d([-1,0,1,2],[0.001,0.0001,0.0001,0.001],fill_value=(1,1))
        s_for_L=interp1d([-1,0,1,2],[0.001,0.0001,0.0001,0.001],fill_value=(1,1))
        max_Gn=max(Gn_vector)
        max_A=max(A_vector)
        max_L=max(L_vector)

    G_rel=UnivariateSplineModified(rotations,[x/max_G for x in G_vector],k=4,s=s_for_G(betta))
    G=f_factory(G_rel,max_G)
    G_der2=G_rel.derivative(2)
    PR_rel=UnivariateSplineModified(rotations,[x/max_PR for x in PR_vector],k=4,s=s_for_PR(betta))
    PR=f_factory(PR_rel,max_PR)
    PR_der2=PR_rel.derivative(2)
    Eff_rel=UnivariateSplineModified(rotations,[x/max_Eff for x in Eff_vector],k=5,s=s_for_Eff(betta))
    Eff=f_factory(Eff_rel,max_Eff)
    Eff_der2=Eff_rel.derivative(2)
    if type_of_map=="turbine":
#        L=Akima1DInterpolatorModified(rotations,L_vector)
#        A=Akima1DInterpolatorModified(rotations,A_vector)
        if len(Gn_vector)>0:
            Gn_rel=UnivariateSplineModified(rotations,[x/max_Gn for x in Gn_vector],k=5,s=s_for_Gn(betta))
            Gn=f_factory(Gn_rel,max_Gn)
            Gn_der2=Gn_rel.derivative(2)
        if len(L_vector)>0:
            L_rel=UnivariateSplineModified(rotations,[x/max_L for x in L_vector],k=5,s=s_for_A(betta))
            L=f_factory(L_rel,max_L)
            L_der2=L_rel.derivative(2)
        if len(A_vector)>0:
            A_rel=UnivariateSplineModified(rotations,[x/max_A for x in A_vector],k=5,s=s_for_L(betta))
            A=f_factory(A_rel,max_A)
            A_der2=A_rel.derivative(2)
    if type_of_map=="turbine":
        _rez= {'G': G(n),'PR': PR(n), 'Eff': Eff(n), 'G_f':G, 'PR_f':PR, 'Eff_f':Eff, 'G_f_der2':G_der2, 'PR_f_der2':PR_der2, 'Eff_f_der2':Eff_der2, 'Rot_v': rotations, 'G_v': G_vector, 'PR_v': PR_vector,'Eff_v': Eff_vector}#для проверки    
        if 'L' in locals():
            _rez['L']=L(n)
            _rez['L_f']=L
            _rez['L_v']=L_vector
            _rez['L_f_der2']=L_der2
        if 'A' in locals():
            _rez['A']=A(n)
            _rez['A_f']=A
            _rez['A_v']=A_vector
            _rez['A_f_der2']=A_der2
        if 'Gn' in locals():
            _rez['Gn']=Gn(n)
            _rez['Gn_f']=Gn
            _rez['Gn_v']=Gn_vector
            _rez['Gn_f_der2']=Gn_der2
    elif type_of_map=='compressor':
        _rez= {'G': G(n),'PR': PR(n), 'Eff': Eff(n), 'G_f':G, 'PR_f':PR, 'Eff_f':Eff,'G_f_der2':G_der2, 'PR_f_der2':PR_der2, 'Eff_f_der2':Eff_der2, 'Rot_v': rotations, 'G_v': G_vector, 'PR_v': PR_vector,'Eff_v': Eff_vector}#для проверки    
    
    return _rez

#rez=Parameters_out(-0.1,1)    
      



#    1) проходимся по всем заданным веткам оборотов, задаем nx
#    2) строим функцию зависимости выбранного параметрв от бетта
#    3) проходимся по всем бетта
#    4) по заданной PR и n находим все искомые параметры
#    5) группируем все полученные значения как трехмерную функцию зависимости всех параметров от оборотов и бетта
#    RectBivariateSpline, interp2d



#6.1) проверяем поветочно. Т.е. строим графики исходных данных (обозначены точками) и обработанных кривых отдельно для каждой ветки бетта
bbb=np.linspace(-0.5,1.5,21)
# 
# if type_of_map=="turbine":
#     fig4, axes4 = plt.subplots(5,1)
# elif type_of_map=='compressor':
#     fig4, axes4 = plt.subplots(3,1)
    

quantity_of_betta=len(bbb)#для этого сначала надо знать количество напорных веток    
colors = [cmap(i) for i in np.linspace(0, 1, quantity_of_betta)]
plot_G=[]
scatter_G=[]
plot_PR=[]
scatter_PR=[]
plot_Eff=[]
scatter_Eff=[]
if type_of_map=="turbine":
    plot_Gn=[]
    scatter_Gn=[]
    plot_A=[]
    scatter_A=[]
    plot_L=[]
    scatter_L=[]

for ind,betta_i_colors in enumerate(zip(bbb,colors)):
    betta_i=betta_i_colors[0]
    color=betta_i_colors[1]
    rez=Parameters_out(betta_i,1)
    G_f=rez['G_f']
    PR_f=rez['PR_f']
    Eff_f=rez['Eff_f']
    G_f_der2=rez['G_f_der2']
    PR_f_der2=rez['PR_f_der2']
    Eff_f_der2=rez['Eff_f_der2']
    if type_of_map=="turbine":
        if 'Gn_f' in rez:
            Gn_f=rez['Gn_f']
            Gn_f_der2=rez['Gn_f_der2']
        if 'A_f' in rez:
            A_f=rez['A_f']
            A_f_der2=rez['A_f_der2']
        if 'L_f' in rez:
            L_f=rez['L_f']
            L_f_der2=rez['L_f_der2']
    rot_v=rez['Rot_v']
    G_v=rez['G_v']
    PR_v=rez['PR_v']
    Eff_v=rez['Eff_v']
    if type_of_map=="turbine":
        if "Gn_v" in rez:
            Gn_v=rez['Gn_v']
        if "A_v" in rez:
            A_v=rez['A_v']
        if "L_v" in rez:
            L_v=rez['L_v']
    rot_v2=np.linspace(rot_v[0],rot_v[-1],100)
    G_v2=[]
    PR_v2=[]
    Eff_v2=[]
    G_v2_der2=[]
    PR_v2_der2=[]
    Eff_v2_der2=[]
    if type_of_map=="turbine":
        Gn_v2=[]
        A_v2=[]
        L_v2=[]  
        Gn_v2_der2=[]
        A_v2_der2=[]
        L_v2_der2=[]
    for n_i in rot_v2:
        G_v2.append(G_f(n_i))
        G_v2_der2.append(G_f_der2(n_i))
        PR_v2.append(PR_f(n_i))
        PR_v2_der2.append(PR_f_der2(n_i))
        Eff_v2.append(Eff_f(n_i))
        Eff_v2_der2.append(Eff_f_der2(n_i))
        if type_of_map=="turbine":
            if "Gn_f" in globals():
                Gn_v2.append(Gn_f(n_i))
                Gn_v2_der2.append(Gn_f_der2(n_i))
            if "A_f" in globals():
                A_v2.append(A_f(n_i))
                A_v2_der2.append(A_f_der2(n_i))
            if 'L_f' in globals():
                L_v2.append(L_f(n_i))
                L_v2_der2.append(L_f_der2(n_i))
    if type_of_map=="compressor":
        plot_G.append({'x':rot_v2,'y':G_v2,'label':betta_i,'c':color})
        scatter_G.append({'x':rot_v,'y':G_v,'c':color})
        
    if type_of_map=="turbine":
        plot_Gn.append({'x':rot_v2,'y':Gn_v2,'label':betta_i,'c':color})
        scatter_Gn.append({'x':rot_v,'y':Gn_v,'c':color})
        plot_A.append({'x':rot_v2,'y':A_v2,'label':betta_i,'c':color})
        scatter_A.append({'x':rot_v,'y':A_v,'c':color})
        plot_L.append({'x':rot_v2,'y':L_v2,'label':betta_i,'c':color})
        scatter_L.append({'x':rot_v,'y':L_v,'c':color})
        # points_for_plot=[{'x':rot_v2,'y':G_v2,'label':betta_i,'c':color}]
        # points_for_scatter=[{'x':rot_v,'y':G_v,'label':betta_i,'c':color}]
        # _fig3=chart.Chart(points_for_scatter=points_for_scatter,points_for_plot=points_for_plot,title='{}'.format('G=f(n) при разных betta'),ylabel='G',xlabel='n',dpi=150,figure_size=(14,21))
    plot_PR.append({'x':rot_v2,'y':PR_v2,'label':betta_i,'c':color})
    scatter_PR.append({'x':rot_v,'y':PR_v,'c':color})
    
    plot_Eff.append({'x':rot_v2,'y':Eff_v2,'label':betta_i,'c':color})
    scatter_Eff.append({'x':rot_v,'y':Eff_v,'c':color})
    if type_of_map=="turbine":
        _fig3=chart.Chart(points_for_scatter=[{'x':rot_v,'y':Gn_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':Gn_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('Gn=f(n).','Ветка betta=',betta_i),ylabel='Gn',xlabel='n',dpi=150,figure_size=(17,15))        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':G_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':G_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('G=f(n).','Ветка betta=',betta_i),ylabel='G',xlabel='n')        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':PR_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':PR_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('PR=f(n).','Ветка betta=',betta_i),ylabel='RP',xlabel='n')        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':Eff_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':Eff_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('Eff=f(n).','Ветка betta=',betta_i),ylabel='Eff',xlabel='n')        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':A_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':A_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('A=f(n).','Ветка betta=',betta_i),ylabel='A',xlabel='n')        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':L_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':L_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('L=f(n).','Ветка betta=',betta_i),ylabel='L',xlabel='n')        
    if type_of_map=="compressor":
        _fig3=chart.Chart(points_for_scatter=[{'x':rot_v,'y':G_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':G_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('G=f(n).','Ветка betta=',betta_i),ylabel='G',xlabel='n',dpi=150,figure_size=(17,15))        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':PR_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':PR_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('PR=f(n).','Ветка betta=',betta_i),ylabel='RP',xlabel='n')        
        _fig3.add_chart(points_for_scatter=[{'x':rot_v,'y':Eff_v,'c':color}],points_for_plot=[{'x':rot_v2,'y':Eff_v2,'label':betta_i,'c':color}],title='{} {} {}'.format('Eff=f(n).','Ветка betta=',betta_i),ylabel='Eff',xlabel='n')        
    
    
    
    
if type_of_map=="compressor":
    _fig4=chart.Chart(points_for_scatter=scatter_G,points_for_plot=plot_G,title='{} {} {}'.format('G=f(n).','Ветка betta=',betta_i),ylabel='G',xlabel='n',dpi=150,figure_size=(17,15))        
    _fig4=chart.Chart(points_for_scatter=scatter_PR,points_for_plot=plot_PR,title='{} {} {}'.format('PR=f(n).','Ветка betta=',betta_i),ylabel='PR',xlabel='n',dpi=150,figure_size=(17,15))        
    _fig4=chart.Chart(points_for_scatter=scatter_Eff,points_for_plot=plot_Eff,title='{} {} {}'.format('Eff=f(n).','Ветка betta=',betta_i),ylabel='Eff',xlabel='n',dpi=150,figure_size=(17,15))        

if type_of_map=="turbine":
    _fig4=chart.Chart(points_for_scatter=scatter_Gn,points_for_plot=plot_Gn,title='{} {} {}'.format('Gn=f(n).','Ветка betta=',betta_i),ylabel='Gn',xlabel='n',dpi=150,figure_size=(17,15))        
    _fig4=chart.Chart(points_for_scatter=scatter_PR,points_for_plot=plot_PR,title='{} {} {}'.format('PR=f(n).','Ветка betta=',betta_i),ylabel='PR',xlabel='n',dpi=150,figure_size=(17,15))        
    _fig4=chart.Chart(points_for_scatter=scatter_Eff,points_for_plot=plot_Eff,title='{} {} {}'.format('Eff=f(n).','Ветка betta=',betta_i),ylabel='Eff',xlabel='n',dpi=150,figure_size=(17,15))        
    _fig4=chart.Chart(points_for_scatter=scatter_A,points_for_plot=plot_A,title='{} {} {}'.format('A=f(n).','Ветка betta=',betta_i),ylabel='A',xlabel='n',dpi=150,figure_size=(17,15))        
    _fig4=chart.Chart(points_for_scatter=scatter_L,points_for_plot=plot_L,title='{} {} {}'.format('L=f(n).','Ветка betta=',betta_i),ylabel='L',xlabel='n',dpi=150,figure_size=(17,15))        
            

"""
#6.2) строим для проверки графики распределения параметра k в зависимости от оборотов и бетта
n_graph=np.linspace(n.iloc[0]*0.9,n.iloc[-1]*1.1, 100)
betta_graph=np.linspace(-0.2, 1.2, 10)
if type_of_map=="turbine":
    fig2, axes2 = plt.subplots(5,1)
    fig2.set_size_inches(17, 50)
elif type_of_map=='compressor':
    fig2, axes2 = plt.subplots(4,1)
    fig2.set_size_inches(17, 40)
#axes2[0].set_title('k=f(n) при разных бетта Если на графике что-то криво, то нужно проверить исходные данные')
#axes2[0].set_xlabel('Обороты')
#axes2[0].set_ylabel('k=PR/G для компр, k=PR для турбины')
#        axes2.ylabel('')
#for betta_i in betta_graph:
#    k_graph=[]
#    for_graph=my_interp(rotations,betta_i)
#    for ni in n_graph:
#        k_graph.append(for_graph(ni))
#    axes2[0].scatter(n,k,s=10)
#    axes2[0].plot(n_graph,k_graph)
#    axes2[0].legend(betta_graph)
    
    #temp_data=reader.loc[reader.n == 0.8] #выделяем из общего массива данных только те, что относятся к определенным оборотам nx
    #GGG=temp_data.G
    #Efff=temp_data.Eff
    #PRRR=temp_data.PR
    
#oboroty=[x for x in xrange(1, 25, 2)]  
#6.3) строим для проверки графики почти такие же, но это графики в классическом виде PR=f(G)   и Eff=(G)
n_graph2=list(np.arange(n.iloc[0]*0.9,n.iloc[-1]*1.1,0.025))
betta_graph2=list(np.arange(-0.2,1.2,0.025))

#oboroty=list(np.arange(n.iloc[0]*0.9,n.iloc[-1]*1.1,0.01))
for n_i in n_graph2:
    G_gr=[]
    PR_gr=[]    
    Eff_gr=[]  
    if type_of_map=="turbine":
        A_gr=[]
        L_gr=[]
    for betta_i in betta_graph2:
        rez=Parameters_out(betta_i,n_i)
        G_gr.append(rez['G'])
        PR_gr.append(rez['PR'])
        Eff_gr.append(rez['Eff'])
        if type_of_map=="turbine":
            if 'A' in rez:
                A_gr.append(rez['A'])
            if 'L' in rez:
                L_gr.append(rez['L'])
    if type_of_map=="compressor":
        axes2[1].plot(G_gr,PR_gr)
        axes2[2].plot(G_gr,Eff_gr)
        axes2[3].plot(PR_gr,Eff_gr)
    elif type_of_map=="turbine":
        axes2[1].plot(PR_gr,list(map(lambda x: x*n_i,G_gr)))
        axes2[2].plot(PR_gr,Eff_gr)
        if len(A_gr)>0:
            axes2[3].plot(PR_gr,A_gr)
        if len(L_gr)>0:
            axes2[4].plot(PR_gr,L_gr)
        
for betta_i in betta_graph2:
    G_gr=[]
    PR_gr=[]    
    Eff_gr=[]  
    if type_of_map=="turbine":
        A_gr=[]
        L_gr=[]
    for n_i in n_graph2:
        rez=Parameters_out(betta_i,n_i)
        if type_of_map=="turbine":
            G_gr.append(rez['G']*n_i)    
        if type_of_map=="compressor":
            G_gr.append(rez['G'])    
        PR_gr.append(rez['PR'])
        Eff_gr.append(rez['Eff'])
        if type_of_map=="turbine":
            if 'A' in rez:
                A_gr.append(rez['A'])
            if 'L' in rez:
                L_gr.append(rez['L'])
    if type_of_map=="compressor":
        axes2[1].plot(G_gr,PR_gr)
        axes2[2].plot(G_gr,Eff_gr)
        axes2[3].plot(PR_gr,Eff_gr)
    elif type_of_map=="turbine":
        axes2[1].plot(PR_gr,G_gr)
        axes2[2].plot(PR_gr,Eff_gr)
        if len(A_gr)>0:
            axes2[3].plot(PR_gr,A_gr)
        if len(L_gr)>0:
            axes2[4].plot(PR_gr,L_gr)




#axes2[1].legend(oboroty)
#axes2[2].legend(oboroty)
if type_of_map=="compressor":
    axes2[1].scatter(G,PR,s=10)
    axes2[2].scatter(G,Eff,s=10)
    axes2[3].scatter(PR,Eff,s=10)
    axes2[1].set_title('PR=f(G) по результатам обработанной функции')
    axes2[2].set_title('Eff=f(G) по результатам обработанной функции')
    axes2[3].set_title('Eff=f(PR) по результатам обработанной функции')
if type_of_map=="turbine":
    axes2[1].scatter(PR,Gn,s=10)
    axes2[2].scatter(PR,Eff,s=10)
    axes2[1].set_title('G=f(PR) по результатам обработанной функции')
    axes2[2].set_title('Eff=f(PR) по результатам обработанной функции')
    if 'A' in reader:
        axes2[3].scatter(PR,A,s=10)
    if 'L' in reader:
        axes2[4].scatter(PR,L,s=10)
#    axes2[3].legend(oboroty)
#    axes2[4].legend(oboroty)
    axes2[3].set_title('Alfa=f(PR) по результатам обработанной функции')
    axes2[4].set_title('Lambda=f(PR) по результатам обработанной функции')


betta_test=0
n_test=0.8
rez=Parameters_out(betta_test,n_test)  
print('Пример выполнения функции:','betta=',betta_test,'n=',n_test,'G=',rez['G'],'PR=',rez['PR'],'Eff=',rez['Eff'])
betta_test=1
n_test=0.8
rez=Parameters_out(betta_test,n_test)  
print('Пример выполнения функции:','betta=',betta_test,'n=',n_test,'G=',rez['G'],'PR=',rez['PR'],'Eff=',rez['Eff'])

"""
#7) формируем массив обработанных данных для использования в моделях в дальнейшем


size_n=100
size_betta=100
n_min=rotations[0]-0.0
n_max=rotations[-1]+0.0
betta_min=-0.0
betta_max=1.0

n_mainrezult=np.linspace(n_min, n_max, size_n)
betta_mainrezult=np.linspace(betta_min,betta_max, size_betta)

G_mainrezult=np.empty([size_n,size_betta])
PR_mainrezult=np.empty([size_n,size_betta])
Eff_mainrezult=np.empty([size_n,size_betta])
if type_of_map=="turbine":
    A_mainrezult=np.empty([size_n,size_betta])
    L_mainrezult=np.empty([size_n,size_betta])
for ind_n, n_i in enumerate(n_mainrezult):
    for ind_betta, betta_i in enumerate(betta_mainrezult):
        rez=Parameters_out(betta_i,n_i)
        G_mainrezult[ind_n, ind_betta]=rez['G']
        PR_mainrezult[ind_n,ind_betta]=rez['PR']
        Eff_mainrezult[ind_n,ind_betta]=rez['Eff'] #if (rez['Eff']>0.05) else 0.05
        if type_of_map=="turbine":
            if 'A' in rez:
                A_mainrezult[ind_n,ind_betta]=rez['A']
            if 'L' in rez:
                L_mainrezult[ind_n,ind_betta]=rez['L']
if type_of_map=="turbine":
    main_rezult=[n_mainrezult,betta_mainrezult,G_mainrezult,PR_mainrezult,Eff_mainrezult]
    if 'A_mainrezult' in globals():
        main_rezult.append(A_mainrezult)
    if 'L_mainrezult' in globals():
        main_rezult.append(L_mainrezult)
elif type_of_map=="compressor":
    main_rezult=[n_mainrezult,betta_mainrezult,G_mainrezult,PR_mainrezult,Eff_mainrezult]
#7.1)проверим правильно ли работают функции интерполяции

#!!! каждый раз стоит утонять птребный диапазон массива bbox TODO!!! нужно исследовать возможность оптимизации параметра s и k
Eff_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, Eff_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.0001)
G_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, G_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.0001)
PR_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, PR_mainrezult,bbox=[n_min, n_max, betta_min, betta_max], kx=3, ky=3, s=0.0001)
if type_of_map=='turbine':
    A_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, A_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=5, ky=5, s=0.0001)
    L_Func4=RectBivariateSpline(n_mainrezult,betta_mainrezult, L_mainrezult, bbox=[n_min, n_max, betta_min, betta_max], kx=5, ky=5, s=0.0001)
print("проверяем. PR должна монотонно возрастать или уменьшаться вдоль ветки")
print(PR_Func4(1,0.0),PR_Func4(1,0.25),PR_Func4(1,0.5),PR_Func4(1,0.75),PR_Func4(1,1))
#8)сохраняем полученный список с данными характеристик в сериализированный файл. 
# В списке хранятся данные в следующей последовательности:[n(вектор),betta(вектор),G(n*betta),PR(n*betta),Eff(n*betta)]
name_of_file=name_of_file[:-4]+'_output.dat'

with open(name_of_file.split('\\')[1], 'wb') as f:
    pickle.dump(main_rezult, f)

#with open(name_of_file, 'rb') as f:
#    data_new = pickle.load(f)

ni = np.linspace(n_min, n_max, size_n*10)
ni2 = np.arange(n_min, n_max+0.0001, 0.01)
bi = np.linspace(betta_min, betta_max, size_betta*10)
bi2 = np.arange(betta_min, betta_max+0.00001, 0.1)
nv,bv=np.meshgrid(ni, bi)
PRv=PR_Func4(ni,bi)
Gv=G_Func4(ni,bi)
Effv=Eff_Func4(ni,bi)
PRv2=PR_Func4(ni2,bi)
Gv2=G_Func4(ni2,bi)
PRv3=PR_Func4(ni,bi2)
Gv3=G_Func4(ni,bi2)
PRv2=np.transpose(PRv2)
Gv2=np.transpose(Gv2)

fig3, axes3 = plt.subplots(1,dpi=150)
fig3.set_size_inches(30, 20)
max_eff=scales['Eff']
lev = [0.7,0.8,0.81,0.82,0.83,0.84,0.85,0.86,0.87,0.88,0.885,0.89,0.895,0.9] #!!!!!!! при необходимости подправить значения изолиний кпд
# lev=np.linspace(0.2,max_eff*1.01,num=15)

if type_of_map=='compressor':
    CS=axes3.contourf(Gv,PRv,Effv,levels=lev,cmap='jet')
    CS2=axes3.contour(Gv,PRv,Effv,levels=lev,colors='black',linewidths=0.5)
    axes3.clabel(CS2, inline=1, fontsize=10,colors='k')
    # axes3.scatter(Gv,PRv,color='black',s=0.1)
    axes3.plot(Gv2,PRv2,color='black',linewidth=1.2,linestyle='dotted')
    axes3.plot(Gv3,PRv3,color='black',linewidth=1.2,linestyle='dotted')
    axes3.set_xlabel('G, кг/с',fontsize=20)
    axes3.set_ylabel('PR',fontsize=20)
    for i,nx in enumerate(ni2):
        axes3.text(Gv2[0,i]-0.02,PRv2[0,i]+0.05,np.round(nx,3),fontsize=14)
    for i,bettax in enumerate(bi2):
        axes3.text(Gv3[-1,i]+0.0,PRv3[-1,i]+0.05,np.round(bettax,2),fontsize=14)
    # axes3.set_xlim([0,max(reader.G)*1.2])
    # axes3.set_ylim([0,max(reader.PR)*1.2])
elif type_of_map=='turbine':
    CS=axes3.contourf(PRv,(Gv.transpose()*ni).transpose(),Effv,levels=lev,cmap='jet')
    CS2=axes3.contour(PRv,(Gv.transpose()*ni).transpose(),Effv,levels=lev,colors='black',linewidths=0.5)
    axes3.clabel(CS2, inline=1, fontsize=10,colors='k')
    # axes3.scatter(PR,Gn,color='black',s=5)
    Gnv2=[]
    for _betta_const in Gv2:
        _temp=_betta_const*ni2
        Gnv2.append(_temp)
    Gnv2=np.array(Gnv2)
    Gnv3=(Gv3.transpose()*ni).transpose()
    # axes3.plot(PRv2,Gnv2,color='black',linewidth=1.2,linestyle='dotted',label=(0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0))
    axes3.plot(PRv3,Gnv3,color='black',linewidth=1.2,linestyle='dotted',label=(0,0.2,0.4,0.6,0.8,1))
    axes3.set_ylabel('G*n',fontsize=20)
    axes3.set_xlabel('PR',fontsize=20)
    for i,nx in enumerate(ni2):
        axes3.text(PRv2[0,i]-0.1,Gnv2[0,i]-0.002,np.round(nx,3),fontsize=14)
    for i,bettax in enumerate(bi2):
        axes3.text(PRv3[-1,i],Gnv3[-1,i]+0.001,np.round(bettax,2),fontsize=14)
    # axes3.set_xlim([0,max(reader.PR)*1.2])
    # axes3.set_ylim([0,max(reader.Gn)*1.2])

axes3.grid()
#axes3.legend()

   
quantity_of_rotations=len(rotations)#для этого сначала надо знать количество напорных веток    
colors = [cmap(i) for i in np.linspace(0, 1, quantity_of_rotations)]

plotPRG=[]
scatterPRG=[]
plotGEff=[]
scatterGEff=[]
plotPREff=[]
scatterPREff=[]
plotPRA=[]
scatterPRA=[]
plotPRL=[]
scatterPRL=[]
for ni_color in zip(rotations,colors):
    ni=ni_color[0]
    color=ni_color[1]
    Gvect=[]
    PRvect=[]
    Effvect=[]
    Avect=[]
    Lvect=[]
    G_points=initial_reader.G[initial_reader.n==ni]
    if type_of_map=='turbine':
        Gn_points=initial_reader.Gn[initial_reader.n==ni]
        A_points=initial_reader.A[initial_reader.n==ni]
        L_points=initial_reader.L[initial_reader.n==ni]
    PR_points=initial_reader.PR[initial_reader.n==ni]
    Eff_points=initial_reader.Eff[initial_reader.n==ni]
    for betta in np.linspace(0.0, 1.0, 50):
        #сначала строим ветку
        if type_of_map=='compressor':
            Gvect.append(float(G_Func4(ni,betta)))    
        if type_of_map=='turbine':
            Gvect.append(float(G_Func4(ni,betta))*ni)    
            Avect.append(float(A_Func4(ni,betta)))    
            Lvect.append(float(L_Func4(ni,betta)))    
        PRvect.append(float(PR_Func4(ni,betta)))
        Effvect.append(float(Eff_Func4(ni,betta)))
    if type_of_map=='compressor':
        plotPRG.append({'x':PRvect,'y':Gvect,'c':color},)
        scatterPRG.append({'x':PR_points,'y':G_points,'c':color},)
        plotGEff.append({'x':Gvect,'y':Effvect,'c':color},)
        scatterGEff.append({'x':G_points,'y':Eff_points,'c':color},)
    if type_of_map=='turbine':
        plotPRG.append({'x':PRvect,'y':Gvect,'c':color},)
        scatterPRG.append({'x':PR_points,'y':Gn_points,'c':color},)
        plotGEff.append({'x':Gvect,'y':Effvect,'c':color},)
        scatterGEff.append({'x':Gn_points,'y':Eff_points,'c':color},)
        plotPRA.append({'x':PRvect,'y':Avect,'c':color},)
        scatterPRA.append({'x':PR_points,'y':A_points,'c':color},)
        plotPRL.append({'x':PRvect,'y':Lvect,'c':color},)
        scatterPRL.append({'x':PR_points,'y':L_points,'c':color},)
    plotPREff.append({'x':PRvect,'y':Effvect,'c':color},)
    scatterPREff.append({'x':PR_points,'y':Eff_points,'c':color},)

chart.Chart(points_for_scatter=scatterPRG,points_for_plot=plotPRG,title='G*n=f(PR): сверяем исходные данные (точки) с итоговой аппроксимирующей функцией',ylabel='Gn',xlabel='PR',dpi=150,figure_size=(17,15))        
chart.Chart(points_for_scatter=scatterGEff,points_for_plot=plotGEff,title='Eff=f(Gn): сверяем исходные данные (точки) с итоговой аппроксимирующей функцией',ylabel='Eff',xlabel='Gn',dpi=150,figure_size=(17,15))        
chart.Chart(points_for_scatter=scatterPREff,points_for_plot=plotPREff,title='Eff=f(PR): сверяем исходные данные (точки) с итоговой аппроксимирующей функцией',ylabel='Eff',xlabel='PR',dpi=150,figure_size=(17,15))        
if type_of_map=='turbine':
    chart.Chart(points_for_scatter=scatterPRA,points_for_plot=plotPRA,title='A=f(PR): сверяем исходные данные (точки) с итоговой аппроксимирующей функцией',ylabel='A',xlabel='PR',dpi=150,figure_size=(17,15))        
    chart.Chart(points_for_scatter=scatterPRL,points_for_plot=plotPRL,title='L=f(PR): сверяем исходные данные (точки) с итоговой аппроксимирующей функцией',ylabel='L',xlabel='PR',dpi=150,figure_size=(17,15))        



#8) создадим функцию, которая будет считать отклонение результирующей функции от исходных точек.
def target_function(var_list,G,PR):
#    n,betta=var
    n,betta=var_list
#    G=0.4
#    PR=3
#    PR=PR_G[0]
#    G=PR_G[1]
#    print(n,betta,G,PR)
    out=[G_Func4(n,betta)[0][0]-G,PR_Func4(n,betta)[0][0]-PR]
    return out
#    return (float((G_Func4(n,betta)-G)**2+(PR_Func4(n,betta)-PR)**2))
    
result=root(target_function,[0.5,0.5],args=(0.4,3))
#result=root(target_function,[0.5,0.5],args=((0.4,3.0)))





# fig = plt.figure()
# fig.set_size_inches(17, 10)
# ax = fig.add_subplot(111, projection='3d')
# colors = [cmap(i) for i in np.linspace(0, 1, 141)]

# ax.scatter3D(reader.G, reader.PR, reader.Eff, s=10, c='black',depthshade=False)   
#ax.plot_trisurf(Gv.flatten(),PRv.flatten(),Effv.flatten(), linewidth=0.2, antialiased=True)
#ax.plot_surface(Gv, PRv, Effv,cmap='jet',shade=False,zsort='min')
# ax.contour3D(Gv, PRv, Effv, 50, cmap='jet')
#ax.plot([0.35,0.4], [2.5,3], [0.7,0.75])
    
#betta=np.linspace(-0.2, 1.2, 100)
#Gvect=G_Func4(rotations,betta)
#Gvect=np.transpose(Gvect)
#PRvect=PR_Func4(rotations,betta)
#PRvect=np.transpose(PRvect)
#Effvect=Eff_Func4(rotations,betta)
#Effvect=np.transpose(Effvect)
#axes5[0].plot(Gvect,Effvect,color='black',linewidth=1.0)
#axes5[0].scatter(G,Eff,color='black',s=5)
#axes5[0].set_ylim([0.6,0.8])
#axes5[0].grid()
#axes5[0].set_xlabel('G, кг/с',fontsize=20)
#axes5[0].set_ylabel('Eff',fontsize=20)
#axes5[1].plot(PRvect,Effvect,color='black',linewidth=1.0)
#axes5[1].scatter(PR,Eff,color='black',s=5)
#axes5[1].set_ylim([0.6,0.8])
#axes5[1].grid()
#axes5[1].set_xlabel('PR',fontsize=20)
#axes5[1].set_ylabel('Eff',fontsize=20)

#if type_of_map=="turbine":
#    fig4, axes4 = plt.subplots(5,1)
#elif type_of_map=='compressor':


