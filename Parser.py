# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 10:55:11 2020

@author: Sundukov
"""

import ast
import numpy as np
import logging
import re
# import math
solverLog=logging.getLogger('solverLog')



class Parser_formula():
    OPERATORS = {'+': (1, 2, lambda y, x: x + y), #здесь хранятся возможные операторы следующим образом: {'знак оператора': (приоритет_чем_больше_тем_выше, количество аргументов, функция lambda)}
                 '-': (1, 2, lambda y, x: x - y),
                 '*': (2, 2, lambda y, x: x * y),
                 '/': (2, 2, lambda y, x: x / y),
                 '^': (3, 2, lambda y, x: x ** y),
                 '<': (0, 2, lambda y, x: x < y),
                 '<=': (0, 2, lambda y, x: x <= y),
                 '>': (0, 2, lambda y, x: x > y),
                 '>=': (0, 2, lambda y, x: x >= y),
                 '==': (0, 2, lambda y, x: x == y),
                 '!=': (0, 2, lambda y, x: x != y),
                 '-unary': (4, 1, lambda x: 0.0 - x)
                 }
    FUNCTIONS = {'sqrt': lambda x: np.sqrt(x),
                  'sin': lambda x: np.sin(x),
                  'cos': lambda x: np.cos(x),
                  'tg': lambda x: np.tan(x),
                  'tan': lambda x: np.tan(x),
                  'arcsin': lambda x: np.arcsin(x),
                  'arccos': lambda x: np.arccos(x),
                  'arctg': lambda x: np.arctan(x),
                  'arctan': lambda x: np.arctan(x),
                  'deg': lambda x: np.degrees(x),
                  'rad': lambda x: np.radians(x),
                  'log': lambda x: np.log(x),
                  'ln': lambda x: np.log(x),
                  'log10': lambda x: np.log10(x),
                  'exp': lambda x: np.exp(x)
                  }
    #тут будут храниться функции, задаваемые пользователем
    USER_DEFINED_FUNCTIONS={}
    #возможные типы данных, которые может парсить этот парсер: число, пользовательская функция, стандартная функция, математический оператор, аругмент пользовательской функции, параметр объекта, скобки
    POSSIBLE_TYPES=frozenset(['num','udf','st_fun','op','arg','par','br'])

    def __init__(self,link_to_extract=False):
        self.base_link_to_extract=link_to_extract #тут будет хранитсья ссылка на базовые объект, отоносительно котрого будут задаваться параметры
        self.string_formula=np.nan #текстовая формула в человеческом виде
        if self.base_link_to_extract==False:
            solverLog.error('ERROR: Parser_formula did not get link_to_extract')
            raise SystemExit
        self.polish_formula=[] #вычисляемая формула в польской записи
        self.temp_stack_for_calculation=[]#тут будет храниться стек используемый для вычисления формулы в польской записи, если все правильно посчитано, то в стеке будет одно значение - результат вычисления
        self.ARGUMENTS={} #словарь имен аргументов, используемых в функции. Здесь ключ - имя аргумента, значение - ссылка на объект откуда нузно брать числовое значение
        # тут будем хранить направлятор на методы, которые знают как обращаться с разными типами данных
        self.CALC_METHODS = {'num': self.calc_numb,
                        'udf': self.calc_udf,
                        'st_fun': self.calc_st_fun,
                        'op': self.calc_op,
                        'arg': self.calc_arg,
                        'par': self.calc_par}

    #здесь заранее подготавливаем формулу в виде массива, где какие-то переменные на момент подготовки массива могут быть неизвестны, они будут известны потом в процессе расчета, на момент подготовки на эти переменные должны быть сохранены ссылки
    def prepare_formula(self, formula_string): #этот метод вызывается в разделе формул, которые определяется пользователь вида F(x,y,...)=x+y+... В методе разбирается только часть левее знака равно, и вызывается отдельный метод для разбора правой части уравнения
        LHS,RHS=formula_string.split('=',maxsplit=1) #разделяем строку с функцией на имя LHS и параметры и собственно саму формулу RHS
        _rez=re.search(r'([a-zA-Z0-9_]+)\({1}(.*)\){1}',LHS)
        name_of_function = _rez.group(1)
        string_with_arguments = _rez.group(2)
        for arg in string_with_arguments.split(','): #сохраняем имена аргументов, но пока не знаем их числовых значений
            if arg:
                self.ARGUMENTS[arg]=None
        Parser_formula.USER_DEFINED_FUNCTIONS[name_of_function] = self #сохраняем готовую для расчета формулу в словарь класса
        self.string_formula = RHS
        self.prepare_RHS_of_formula(RHS)
        return {name_of_function:self} #и возвращаем наружу на всякий случай
    #Генератор, получает на вход строку, возвращает числа в формате float, операторы и скобки в формате символов или ссылки/параметры в виде текстовой строки.
    def parse_string_to_generator(self, formula_string):
        digit = '' #в этой переменной будем собирать число, если эта переменная не пустая, то сейчас число находится в процессе сборки
        string_parameter='' #в этом переменной будем собирать имя параметра, если эта переменная не пустая, то сейчас она находится в процессе сборки
        udf='' #в этой штуке будем собирать пользовательскую функцию с параметрами вида function(x=...,y=...,...)
        operator_string='' #в этой штуке будем собирать оператор
        last_s='' #тут будем хранить предыдущий параметр s
        open_brackets=int(0) #тут будеи контролировать количество открытых/закрытых скобок
        #возможные типы данных возвращаемые этим парсером:
        #number - число
        #parameter_of_object - строка, содержащая ссылку на параметр внутри объекта self.base_link_to_extract
        #user_defined_function - строка, содержащая имя пользовательской функции и после в скобках перечисление аргументов этой функции и откуда брать значения для этих аргументов
        #standart_function - строка, содержащая имя стандартной функции
        #argument_of_function - строка содержащая имя аргумента функции, значение этого аргумента на момент парсенья может быть неизвестно
        #operator - строка с оператором
        #() - скобки
        for s in formula_string:
            if not operator_string:
                #1) если символ - цифра или точка и строка string_parameter пустая, то собираем число
                if s in '1234567890.' and not string_parameter and not udf:
                    # print('111')
                    digit += s
                    last_s=s
                    continue
                elif digit: # если символ не цифра, то выдаём собранное число и начинаем собирать заново
                    # print('111a')
                    # x=dict(number=float(digit))
                    yield 'num',digit
                    digit = ''
                #2) если символ - буква, цифра или точка/нижнее подчеркивание и число пустое, то собираем из нее имя параметра, имя оператора, имя аргумента, имя функции дальше нужно распознать что конкретно
                if not udf and (s.isalpha() or s == '_'): #ловим первый символ из строки, первый символ обязательно буква или _
                    string_parameter+=s
                    last_s = s
                    continue
                elif string_parameter and not udf and (s.isalnum() or (s in '_.')): #если уже тточно знаем что начали собирать строку, то ищем последующие симолы, ими могут быть цифры, буквы, _ или .
                    string_parameter+=s
                    last_s = s
                    continue
                elif string_parameter and not udf and (s == '('):
                    if string_parameter in Parser_formula.FUNCTIONS:
                        yield 'st_fun',string_parameter
                        string_parameter = ''
                    elif string_parameter in Parser_formula.USER_DEFINED_FUNCTIONS:
                        udf=string_parameter
                        string_parameter=''
                    elif self.check_exist_parameter_in_obj(string_parameter) and string_parameter in self.ARGUMENTS:
                        solverLog.error(f'Error: formula {self.string_formula} has duplicated string {string_parameter} in arguments of formula and in parameters of object {self.base_link_to_extract}')
                        raise SystemExit
                    elif self.check_exist_parameter_in_obj(string_parameter):
                        yield 'par',string_parameter
                        string_parameter = ''
                    elif string_parameter in self.ARGUMENTS:
                        yield 'arg',string_parameter
                        string_parameter=''
                    else:
                        # yield 'unknown_object',string_parameter
                        # string_parameter = ''
                        solverLog.error(f"Error: formula {self.string_formula} has unknown object '{string_parameter}'")
                        raise SystemExit
                elif string_parameter and not udf and (s in '+-*/^=<>!_)'):
                    if self.check_exist_parameter_in_obj(string_parameter) and string_parameter in self.ARGUMENTS:
                        solverLog.error(f'Error: formula {self.string_formula} has duplicated string {string_parameter} in arguments of formula and in parameters of object {self.base_link_to_extract}')
                        raise SystemExit
                    elif self.check_exist_parameter_in_obj(string_parameter):
                        yield 'par',string_parameter
                        string_parameter = ''
                    elif string_parameter in self.ARGUMENTS:
                        yield 'arg',string_parameter
                        string_parameter=''
                    else:
                        # yield 'unknown_object', string_parameter
                        # string_parameter = ''
                        solverLog.error(f"Error: formula {self.string_formula} has unknown object '{string_parameter}'")
                        raise SystemExit


                #3) собираем пользовательскую формулу в виде function(x=...,y=...,...)
                if udf and (s in '+-*/^=<>!.,(_' or s.isalnum()):
                    if s=='(':
                        open_brackets+=1
                    udf+=s
                    last_s=s
                    continue
                elif udf and s==')':
                    open_brackets-=1
                    udf += s
                    if open_brackets==0:
                        yield 'udf',udf
                        udf=''
                    last_s = s
                    continue

            #4) собираем оператор
            if s in "+-*/^=<>!()":
                if s=='-' and (last_s =='' or last_s in Parser_formula.OPERATORS or last_s == "("):
                    s='-unary'
                    yield 'op',s
                    last_s=s
                    continue

                if s in '<>=!' and not operator_string:
                    operator_string += s
                    last_s = s
                    continue
                elif operator_string:
                    if s=='=':
                        yield 'op',operator_string+s
                        last_s = s
                        operator_string = ''
                        continue
                    else:
                        yield 'op',operator_string
                        operator_string = ''

                if s in "()":
                    yield 'br',s
                    last_s = s
                    continue
                else:
                    yield 'op',s
                    last_s = s
            else:
                solverLog.error(f"Error: formula {self.string_formula} has unknown object '{s}'")
                raise SystemExit

        if digit:  # если в конце строки есть число, выдаём его
            yield 'num',digit
        if string_parameter:
            if string_parameter in Parser_formula.USER_DEFINED_FUNCTIONS:
                yield 'udf',string_parameter
            elif self.check_exist_parameter_in_obj(string_parameter) and string_parameter in self.ARGUMENTS:
                solverLog.error(f'Error: formula {self.string_formula} has duplicated string {string_parameter} in arguments of formula and in parameters of object {self.base_link_to_extract}')
                raise SystemExit
            elif self.check_exist_parameter_in_obj(string_parameter):
                yield 'par', string_parameter
            elif string_parameter in self.ARGUMENTS:
                yield 'arg', string_parameter
            else:
                solverLog.error(f"Error: formula {self.string_formula} has unknown object '{string_parameter}'")
                raise SystemExit
        if udf:
            yield 'udf', udf
        if operator_string:
            yield 'op', operator_string

    #Генератор, получает на вход итерируемый объект из чисел и операторов в инфиксной нотации, возвращает числа и операторов в обратной польской записи в объект self.polish_formula
    def shunting_yard(self,parsed_formula):
        stack = []  # в качестве основного стэка используем список
        self.polish_formula = [] #тут будет хранить итоговую формулу в польской нотации для вычисления (в виде массива)
        for token in parsed_formula:
            # if isinstance(_token,str):
            #     _rez = re.search(r'([a-zA-Z0-9_.]+)(?:\({1}(.+)\){1})?', token)
            #     token = _rez.group(1)
            #     token_with_parameters = _rez.group(2)
            # else:
            #     token=token
            #Сначала проверяем если в токене оператор или скобки
            # если элемент - оператор, то отправляем дальше все операторы из стека, 
            # чей приоритет больше или равен пришедшему,
            # до открывающей скобки или опустошения стека.
            # здесь мы пользуемся тем, что все операторы право-ассоциативны
            if token[0] == 'op':
                while stack and stack[-1][1] != "(" and ((stack[-1][1] in Parser_formula.OPERATORS and #если последний значение в стеке - это ператор И приоритет его больше или равен оператору из токена
                          Parser_formula.OPERATORS[token[1]][0] <= Parser_formula.OPERATORS[stack[-1][1]][0]) or #ИЛИ последнее значение в стеке - это стандартная функция
                         (stack[-1][1] in Parser_formula.FUNCTIONS)):
                    self.polish_formula.append(stack.pop()) #то добавляем в польскую запись последнее значение из стека
                stack.append(token)
                continue
            elif token[1] == ")":
                # если элемент - закрывающая скобка, выдаём все элементы из стека, до открывающей скобки,
                # а открывающую скобку выкидываем из стека.
                while stack:
                    x = stack.pop()
                    if x[1] == "(":
                        break
                    self.polish_formula.append(x)
                continue
            elif token[1] == "(":
                # если элемент - открывающая скобка, просто положим её в стек
                stack.append(token)
                continue
            elif token[0] == 'num':
                token=(token[0],float(token[1]))
                self.polish_formula.append(token)
                continue

            #если дошли до сюда, значит в токене нет ни операторов, ни чисел, ни скобок
            #проверяем являестя ли токен стандартной функцией, пользовательской ф-ей, аргументом функции, либо строкой указывающей на како-либо объект, либо числом, либо ссылкой на объект
            if token[0] == 'st_fun':
                stack.append(token)
            elif token[0] == 'udf':
                udf_name,args=token[1].split('(',1)
                args_list=args.split(')',1)[0].split(',')
                args_dict={}
                for _arg in args_list:
                    key,val=_arg.split('=')
                    args_dict[key]= self.str2link(val)
                token=(token[0],(udf_name,args_dict))
                self.polish_formula.append(token)
            # elif token[0] in self.ARGUMENTS.keys():
            #     self.polish_formula.append(token)
            elif token[0] == 'par':
                token=(token[0],self.str2link(token[1]))
                self.polish_formula.append(token)
            else:
                # если элемент - не является ни оператором, ни функцией, т.е. вероятно это ссылка на объект, отправим его сразу на выход
                self.polish_formula.append(token)
            # else:
            #     solverLog.error(f"Error: Parser_formula: unparseble symbols {token} in formula {self.string_formula}")
            #     raise raise SystemExit

        while stack:
            self.polish_formula.append(stack.pop())
        self.polish_formula=tuple(self.polish_formula)
        for token in self.polish_formula:
            if token[0] not in Parser_formula.POSSIBLE_TYPES:
                solverLog.error(f"Error: Parser_formula: unknown type of token {token[1]} in formula {self.string_formula}")
                raise SystemExit

    # вспомогательная функция для преобразования строки, содержащей ссылку на параметр в tuple, где первое значение хранит указатель на объект, а второе значение - имя параметры этого объекта, значение которого нужно узнать. Так странно сделано из-за того, что в питоне есть mutable и immutable переменные
    # если скормить строку, в которой число - вернет float, если скормить tuple со ссылкой - попытаестя его вычислить
    def str2link(self,string):
        if isinstance(string,tuple):
            return self.calc_par(string)
        elif self.is_number(string):
            return float(string)
        else:
            rez=self.base_link_to_extract
            broken_string = string.split('.')
            for val in broken_string[:-1]:
                if hasattr(rez,val):
                    rez=getattr(rez,val)
                else:
                    return 'unknown parameter '+string
        return (rez,broken_string[-1])

    def is_number(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def check_exist_parameter_in_obj(self,string):
        rez=self.base_link_to_extract
        broken_string = string.split('.')
        for val in broken_string:
            if hasattr(rez,val):
                rez=getattr(rez,val)
            else:
                return False
        return True

    #Функция, получает на вход итерируемый объект чисел и операторов в обратной польской нотации, возвращает результат вычисления:
    def calculate(self):
        for key,value in self.ARGUMENTS.items():
            if value==None or value==np.nan:
                solverLog.error(f'ERROR: unknown value for argument {key} in user defined formula {self.string_formula}')
                raise SystemExit

        self.temp_stack_for_calculation = []
        for token in self.polish_formula:
            self.temp_stack_for_calculation.append(self.CALC_METHODS[token[0]](token[1]))
        return self.temp_stack_for_calculation[0] # результат вычисления - единственный элемент в стеке

    def prepare_RHS_of_formula(self,RHS):#этот метод вызывается в разделе, где формулы задаются для параметров, т.е. у формул нет имени и аргументов
        self.shunting_yard(self.parse_string_to_generator(RHS)) #сохраняем формулу в виде польской нотации в self.polish_formula

    def insert_values_in_arguments(self,**dict_of_values):
        for arg,value in dict_of_values.items():
            if arg in self.ARGUMENTS.keys():
                self.ARGUMENTS[arg]=self.str2link(value)
            else:
                solverLog.error(f'ERROR: unknown name of argument {arg} in attempt to insert value {value} in formula {self.string_formula}')

    def calc_numb(self,number):
        return number

    def calc_udf(self,name_and_args):
        Parser_formula.USER_DEFINED_FUNCTIONS[name_and_args[0]].insert_values_in_arguments(**name_and_args[1])
        rez= Parser_formula.USER_DEFINED_FUNCTIONS[name_and_args[0]].calculate()
        for key in Parser_formula.USER_DEFINED_FUNCTIONS[name_and_args[0]].ARGUMENTS.keys():
            Parser_formula.USER_DEFINED_FUNCTIONS[name_and_args[0]].ARGUMENTS[key]=np.nan
        return rez

    def calc_st_fun(self,function):
        return Parser_formula.FUNCTIONS[function](self.temp_stack_for_calculation.pop())

    def calc_op(self,operator):
        list_of_args = [self.temp_stack_for_calculation.pop() for i in range(Parser_formula.OPERATORS[operator][1])]
        return Parser_formula.OPERATORS[operator][2](*list_of_args)

    def calc_arg(self,argument):
        return self.str2link(self.ARGUMENTS[argument])

    def calc_par(self,parameter):
        val = float(getattr(parameter[0], parameter[1]))
        if np.isnan(val):
            solverLog.error(
                'Error: Undefined parameter ' + parameter + ' = ' + str(val) + ' in function "' + self.string_formula + '"')
            raise SystemExit
        return val


        # if isinstance(token, float):
        #     stack.append(token)
        # elif token in Parser_formula.OPERATORS.keys():  # если приходящий элемент - оператор,
        #     list_of_args = []
        #     for i in range(Parser_formula.OPERATORS[token][1]):
        #         list_of_args.append(stack.pop())
        #     stack.append(Parser_formula.OPERATORS[token][2](*list_of_args))  # вычисляем оператор, возвращаем в стек
        #     # elif token in Parser_formula.UNARY_OPERATORS:
        #     #     x=stack.pop()
        #     #     stack.append(Parser_formula.UNARY_OPERATORS[token][1](x))  # вычисляем оператор, возвращаем в стек
        # elif token in Parser_formula.FUNCTIONS.keys():
        #     stack.append(Parser_formula.FUNCTIONS[token](stack.pop()))
        # elif token in self.ARGUMENTS.keys():
        #     val = self.ARGUMENTS[token]
        #     if isinstance(val, tuple):
        #         val = self.calculate_parameter_of_object(val)
        #     stack.append(val)
        #     self.ARGUMENTS[token] = np.nan
        # elif token in Parser_formula.USER_DEFINED_FUNCTIONS.keys():
        #     # Parser_formula.USER_DEFINED_FUNCTIONS[token].insert_values_in_arguments(z=0.5)
        #     val = Parser_formula.USER_DEFINED_FUNCTIONS[token].calculate()
        #     stack.append(val)
        # elif isinstance(token, tuple):
        #     if isinstance(token[0], str):  # USER_DEFINED_FUNCTION
        #         Parser_formula.USER_DEFINED_FUNCTIONS[token[0]].insert_values_in_arguments(token[1])
        #         val = Parser_formula.USER_DEFINED_FUNCTIONS[token[0]].calculate()
        #     else:  # parameter of object
        #         val = self.calculate_parameter_of_object(token)
        #     stack.append(val)
        # else:
        #     # if isinstance(token, str):
        #     #     val=self.str2parameter(token)
        #     #     if np.isnan(val):
        #     #         solverLog.error('Error: Undefined parameter '+token+' = '+str(val)+' in function "'+self.formula+'"')
        #     #         raise SystemExit
        #     #     stack.append(val)
        #     # else:
        #     stack.append(token)

        #как использовать парсер:
#1) через аргумент инициализатора передать ссылку на базовый объект от которого задаются адреса на другие параметры в форумле
#2) prepare_formula(formula) - передаем строку с формулой.
#3) insert_values_in_arguments(x=4,y='pt.test') - передаем числовые значения для параметров, которые изнаачльно могли быть неизвестны
#4) calculate() - считаем формулу, на выходе д.б. float


class test1():
    def __init__(self):
        self.devices = dict()
        self.air_bleed_out = [{'G_abs_from': 3}, 2, 3]

class test2():
    def __init__(self):
        self.N = [np.nan]
        self.N_offtake = 200
        self.Eff_mech_value = 0.99

a=test1()
a.pt=test2()
a.pt.nnn=test2()
a.devices['pt']=a.pt
a.devices['air_bleed_out']=a.air_bleed_out
a.pt.N_=1000
a.pt.N_offtake=2000
a.pt.Eff_mech_value=0.95
a.pt.test=1
a.x=1
a.y=1


# нужно добавить возможность задавать в формулу имя другой формулы
# добавить возможность использовать формулу задаваемую через точки
# добавить if else

test_formula='function(x_,y_)=1-pt.N_-(-pt.N_offtake*-cos(1+0.57))/(pt.Eff_mech_value+300+ln(20))/1000+x_/y_' #
test_formula2='function2(z)=x+y/z*(-tg(0.8925))+sin(rad(30))+function(x_=4,y_=pt.test)'
test_formula3='1-pt.N-(-pt.N_offtake*-cos(1+0.57))/(pt.Eff_mech_value+300+ln(20))/1000+x/y+test_function(x=1)'
test_formula4='func()=pt.N_-(-pt.N_offtake*-cos(1+0.57))'


b=Parser_formula(a) #задаем через параметр a ссылку на базовые объект откуда будут извлекаться все параметры
b.prepare_formula(test_formula) #задаем строку с формулой
c=Parser_formula(a)
c.prepare_formula(test_formula2) #задаем строку с формулой

# print(b.string_formula)
# print(b.polish_formula)
# print(b.ARGUMENTS)
# print(c.string_formula)
# print(c.polish_formula)
# print(c.ARGUMENTS)
# b.insert_values_in_arguments(x_=4,y_='pt.test')
c.insert_values_in_arguments(z=4)
# print(b.polish_formula)
# print(b.ARGUMENTS)
# print(c.polish_formula)
# print(c.ARGUMENTS)
# print(b.calculate()) #считаем формулу
print(c.calculate())

"""
# класс ниже Parser используется в engine.py для считывания из файла модели строк, где прописывается какие параметры выводить в файл с результатами
# этот класс используется стандартную питоновскую юиюлиотеку ast с сиснтаксическим деревом. Предположительно из-за этого он довольно медленный, поэтому его нельзя использовать в циклах. Для однократного вывода результатов в файл - годится.
class Parser(ast.NodeVisitor):
    tree = None

    _binary_ops = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.Pow: lambda left, right: left ** right
    }

    _unary_ops = {
        ast.UAdd: lambda operand: +operand,
        ast.USub: lambda operand: -operand
    }

    _constants = {
        'None': None,
        'PI': np.pi,
        'pi': np.pi,
        'g': 9.80665
    }

    _functions = {
        'sqrt': np.sqrt,
        'sin': np.sin,
        'cos': np.cos,
        'tg': np.tan,
        'tan': np.tan,
        'arcsin': np.arcsin,
        'arccos': np.arccos,
        'arctg': np.arctan,
        'arctan': np.arctan,
        'deg': np.degrees,
        'rad': np.radians,
        'log': np.log,
        'ln': np.log,
        'log10': np.log10,
        'exp': np.exp
    }

    # def __init__(self):
    #     pass

    def __init__(self, data):  # через data передается ссылка на обек4т, откуда будут извлекаться переменные
        self.data = data
        # def __init__(self, variables=None, functions=None, assignment=False):
        # self._variables = None
        # self.variables = variables
        # self.firstRun = True

        # if functions is None:
        #     self._functions = {}
        # else:
        #     self._functions = functions

        # self._assignment = False
        # self.assignment = assignment

        # self._used_variables = set()
        # self._modified_variables = {}

    def parse(self, expression):

        try:
            self.tree = ast.parse(expression)
            return self.visit(self.tree)
        except SyntaxError as error:
            error.filename = 'filename'
            error.text = expression
            raise error
        except Exception as error:
            error_type = error.__class__.__name__
            if len(error.args) > 2:
                line_col = error.args[1:]
            else:
                line_col = (1, 0)

            error = SyntaxError('{}: {}'.format(error_type, error.args[0]))
            raise error

    def calculate(self):
        return self.visit(self.tree)

    def visit_Module(self, node):
        # print(ast.dump(node))
        return self.visit(node.body[0])

    def visit_Expr(self, node):
        return self.visit(node.value)

    def generic_visit(self, node):
        raise SyntaxError('Node {} not allowed'.format(ast.dump(node)))

    def visit_BinOp(self, node):
        op = type(node.op)
        func = self._binary_ops[op]
        return func(self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node):
        op = type(node.op)
        func = self._unary_ops[op]
        return func(self.visit(node.operand))

    def visit_Num(self, node):
        # pylint: disable=no-self-use
        return float(node.n)

    def visit_Call(self, node):
        name = node.func.id
        if name in self._functions:
            func = self._functions[name]
        else:
            raise NameError("Function '{}' is not defined in parser".format(name), node.lineno, node.col_offset)

        args = [self.visit(arg) for arg in node.args]
        keywords = dict([self.visit(keyword) for keyword in node.keywords])

        # Python 2.7 starred arguments
        # if hasattr(node, 'starargs') and hasattr(node, 'kwargs'):
        #     if node.starargs is not None or node.kwargs is not None:
        #         raise SyntaxError('Star arguments are not supported', ('', node.lineno, node.col_offset, ''))

        return func(*args, **keywords)

    def visit_Name(self, node):
        # print(ast.dump(node))
        if node.id in self._constants:
            # self._used_variables.add(node.id)
            return self._constants[node.id]
        elif node.id in self.data.devices.keys():
            return self.data.devices[node.id]
        elif node.id in self.data.__dict__.keys():
            return getattr(self.data, node.id)
        else:
            return node.id

        # if node.id in self._variable_names:
        #     return self._variable_names[node.id]
        raise NameError("Name '{}' is not defined".format(node.id),
                        node.lineno, node.col_offset)

    def visit_Attribute(self, node):
        # print(ast.dump(node))
        value = self.visit(node.value)
        # print(value)
        # print(node.attr)
        return getattr(value, node.attr)

    def visit_Index(self, node):
        # print(ast.dump(node))
        value = self.visit(node.value)
        if isinstance(value, str):
            return value
        elif isinstance(value, float):
            return int(value)

    def visit_Subscript(self, node):
        # print(ast.dump(node))   
        value = self.visit(node.value)
        ind = self.visit(node.slice)
        return value[ind]

    # def visit_Attribute(self, node):


class test1():
    def __init__(self):
        self.devices = dict()
        self.air_bleed_out = [{'G_abs_from': 3}, 2, 3]


class test2():
    def __init__(self):
        self.N = [np.nan]
        self.N_offtake = 200
        self.Eff_mech_value = 0.99


a = test1()
a.pt = test2()
a.pt.nnn = test2()
a.devices['pt'] = a.pt
a.devices['air_bleed_out'] = a.air_bleed_out
a.pt.N = 1000
a.pt.N_offtake = 2000
a.pt.Eff_mech_value = 0.95

test_formula = 'pt.N-(-pt.N_offtake)/(pt.Eff_mech_value+300+20)/1000'
# stro='air_bleed_out[0][G_abs_from]'
# stro='deg(arctan(1))'
p = Parser(a)
# ee=p.parse(test_formula)
# e=p.calculate()

# print(e)
# print(type(e))
# Expr(value=BinOp(left=Attribute(value=Name(id='pt', ctx=Load()), attr='N', ctx=Load()), op=Sub(), right=BinOp(left=BinOp(left=Attribute(value=Name(id='pt', ctx=Load()), attr='N_offtake', ctx=Load()), op=Div(), right=Attribute(value=Name(id='pt', ctx=Load()), attr='Eff_mech_value', ctx=Load())), op=Div(), right=Num(n=1000))))
"""