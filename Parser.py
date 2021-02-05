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


#класс ниже Parser используется в engine.py для считывания из файла модели строк, где прописывается какие параметры выводить в файл с результатами
 #этот класс используется стандартную питоновскую юиюлиотеку ast с сиснтаксическим деревом. Предположительно из-за этого он довольно медленный, поэтому его нельзя использовать в циклах. Для однократного вывода результатов в файл - годится.
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
    'g':  9.80665 
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
    'exp':np.exp
    }

    # def __init__(self):
    #     pass

    def __init__(self, data): #через data передается ссылка на обек4т, откуда будут извлекаться переменные
        self.data=data
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
    
    
    def visit_Expr(self,node):
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
            return getattr(self.data,node.id)
        else:
            return node.id

        # if node.id in self._variable_names:
        #     return self._variable_names[node.id]
        raise NameError("Name '{}' is not defined".format(node.id),
                        node.lineno, node.col_offset)

    def visit_Attribute(self, node):
        # print(ast.dump(node))
        value=self.visit(node.value)
        # print(value)
        # print(node.attr)
        return getattr(value,node.attr)
    
    def visit_Index(self, node):
        # print(ast.dump(node))
        value=self.visit(node.value)
        if isinstance(value,str):
            return value
        elif isinstance(value,float):
            return int(value)
    
    def visit_Subscript(self, node):
        # print(ast.dump(node))   
        value=self.visit(node.value)
        ind=self.visit(node.slice)
        return value[ind]

    # def visit_Attribute(self, node):

class test1():
    def __init__(self):
        self.devices=dict()
        self.air_bleed_out=[{'G_abs_from': 3},2,3]
        
class test2():
    def __init__(self):
        self.N=[np.nan]
        self.N_offtake=200
        self.Eff_mech_value=0.99

a=test1()
a.pt=test2()
a.pt.nnn=test2()
a.devices['pt']=a.pt
a.devices['air_bleed_out']=a.air_bleed_out
a.pt.N=1000
a.pt.N_offtake=2000
a.pt.Eff_mech_value=0.95


test_formula='pt.N-(-pt.N_offtake)/(pt.Eff_mech_value+300+20)/1000'
# stro='air_bleed_out[0][G_abs_from]'
# stro='deg(arctan(1))'
p = Parser(a)
# ee=p.parse(test_formula)
# e=p.calculate()

# print(e)
# print(type(e))
# Expr(value=BinOp(left=Attribute(value=Name(id='pt', ctx=Load()), attr='N', ctx=Load()), op=Sub(), right=BinOp(left=BinOp(left=Attribute(value=Name(id='pt', ctx=Load()), attr='N_offtake', ctx=Load()), op=Div(), right=Attribute(value=Name(id='pt', ctx=Load()), attr='Eff_mech_value', ctx=Load())), op=Div(), right=Num(n=1000))))

class Parser_formula():
    OPERATORS = {'+': (1, 2, lambda y, x: x + y), #здесь хранятся возможные операторы следующим образом: {'знак оператора': (приоритет_чем_больше_тем_выше, количество аргументов, функция lambda)}
                 '-': (1, 2, lambda y, x: x - y),
                 '*': (2, 2, lambda y, x: x * y),
                 '/': (2, 2, lambda y, x: x / y),
                 '^': (3, 2, lambda y, x: x ** y),
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

    def __init__(self,link_to_extract=False):
        self.base_link_to_extract=link_to_extract #тут будет хранитсья ссылка на базовые объект, отоносительно котрого будут задаваться параметры
        self.string_formula=np.nan #текстовая формула в человеческом виде
        if self.base_link_to_extract==False:
            solverLog.error('ERROR: Parser_formula did not get link_to_extract')
            raise SystemExit
        self.polish_formula=[] #вычисляемая формула в польской записи
        self.ARGUMENTS={} #словарь имен аргументов, используемых в функции. Здесь ключ - имя аргумента, значение - ссылка на объект откуда нузно брать числовое значение
    #Генератор, получает на вход строку, возвращает числа в формате float, операторы и скобки в формате символов или ссылки/параметры в виде текстовой строки.
    def parse_string_to_generator(self, formula_string):
        self.string_formula=formula_string
        number = '' #в этой переменной будем собирать число, если эта переменная не пустая, то сейчас число находится в процессе сборки
        string_parameter='' #в этом переменной будем собирать имя параметра, если эта переменная не пустая, то сейчас она находится в процессе сборки
        last_s='' #тут будем хранить предыдущий параметр s
        for s in formula_string:
            #1) если символ - цифра или точка и строка пустая, то собираем число
            if s in '1234567890.' and not string_parameter:
                # print('111')
                number += s
                last_s=s
                continue
            elif number: # если символ не цифра, то выдаём собранное число и начинаем собирать заново
                # print('111a')
                yield float(number) 
                number = ''
            #2) если символ - буква, цифра или точка/нижнее подчеркивание и число пустое, то собираем из нее имя параметра, имя оператора или имя аргумента, дальше нужно распознать параметр это, оператор, функция или имя аргумента
            if (s.isalnum() or s in '_.') and not number:
                # print('222')
                string_parameter+=s
                last_s = s
                continue
            elif string_parameter: #здксь обнаружили, что строка закончилась и нужно определить что в ней: сслыка на параметр или оператор
                # print('222a')
                yield string_parameter
                string_parameter=''
            #3) если символ - оператор или скобка, то выдаём как есть
            if s in Parser_formula.OPERATORS or s in "()":
                if s=='-' and (last_s =='' or last_s in Parser_formula.OPERATORS or last_s == "("):
                    s='-unary'
                yield s
                last_s = s
            else:
                solverLog.error(f'Forbidden symbol {s} in formula {formula_string}')

        if number:  # если в конце строки есть число, выдаём его
            yield float(number)
        if string_parameter:
            yield string_parameter
    #Генератор, получает на вход итерируемый объект из чисел и операторов в инфиксной нотации, возвращает числа и операторов в обратной польской записи в объект self.polish_formula
    def shunting_yard(self,parsed_formula):
        stack = []  # в качестве основного стэка используем список
        self.polish_formula = [] #тут будет хранить итоговую формулу в польской нотации для вычисления (в виде массива)
        for token in parsed_formula:
            # print(token)
            # если элемент - оператор, то отправляем дальше все операторы из стека, 
            # чей приоритет больше или равен пришедшему,
            # до открывающей скобки или опустошения стека.
            # здесь мы пользуемся тем, что все операторы право-ассоциативны
            if token in Parser_formula.OPERATORS:
                #TODO! почему ниже так сложно? разобраться
                while stack and stack[-1] != "(" and\
                        ((stack[-1] in Parser_formula.OPERATORS and
                          Parser_formula.OPERATORS[token][0] <= Parser_formula.OPERATORS[stack[-1]][0]) or
                         (stack[-1] in Parser_formula.FUNCTIONS)):
                    self.polish_formula.append(stack.pop())
                    #elif stack[-1] in self.USER_FUNCTIONS TODO! тут надо будет предусмотреть возможность использования в формуле пользовательских функций, формируемых как раз за счет этого же парсера
                stack.append(token)
            elif token in Parser_formula.FUNCTIONS:
                stack.append(token)
            elif token == ")":
                # если элемент - закрывающая скобка, выдаём все элементы из стека, до открывающей скобки,
                # а открывающую скобку выкидываем из стека.
                while stack:
                    x = stack.pop()
                    if x == "(":
                        break
                    self.polish_formula.append(x)
            elif token == "(":
                # если элемент - открывающая скобка, просто положим её в стек
                stack.append(token)
            elif isinstance(token, str):
                if token in self.ARGUMENTS.keys():
                    self.polish_formula.append(token)
                else:
                    self.polish_formula.append(self.str2link(token))
            else:
                # если элемент - не является ни оператором, ни функцией, т.е. вероятно это либо число, либо ссылка на объект, отправим его сразу на выход
                self.polish_formula.append(token)
            # print('token: '+str(token))
            # print('stack: '+str(stack))
            # print('polish: '+str(self.polish_formula))
        while stack:
            self.polish_formula.append(stack.pop())
        self.polish_formula=tuple(self.polish_formula)
    def str2parameter(self,string): #вспомогательная функция для преобразования строки, содержащей ссылку на параметр, собственно в значение этого параметра
        broken_string = string.split('.')
        rez=self.base_link_to_extract
        for val in broken_string:
            if hasattr(rez,val):
                rez=getattr(rez,val)
            else:
                return 'unknown parameter '+string
        return rez  
    def str2link(self,string): #вспомогательная функция для преобразования строки, содержащей ссылку на параметр в tuple, где первое значение хранит указатель на объект, а второе значение - имя параметры этого объекта, значение которого нужно узнать. Так странно сделано из-за того, что в питоне есть mutable и immutable переменные
        if type(string) is int or type(string) is float:
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
        
    #Функция, получает на вход итерируемый объект чисел и операторов в обратной польской нотации, возвращает результат вычисления:
    def _calc(self):
        stack = []
        for token in self.polish_formula:
            if token in Parser_formula.OPERATORS:  # если приходящий элемент - оператор,
                list_of_args=[]
                for i in range(Parser_formula.OPERATORS[token][1]):
                    list_of_args.append(stack.pop())
                stack.append(Parser_formula.OPERATORS[token][2](*list_of_args)) # вычисляем оператор, возвращаем в стек
            # elif token in Parser_formula.UNARY_OPERATORS:
            #     x=stack.pop()
            #     stack.append(Parser_formula.UNARY_OPERATORS[token][1](x))  # вычисляем оператор, возвращаем в стек
            elif token in Parser_formula.FUNCTIONS:
                x=stack.pop()
                stack.append(Parser_formula.FUNCTIONS[token](x))
            elif token in self.ARGUMENTS.keys():
                val=self.ARGUMENTS[token]
                if isinstance(val, tuple):
                    val = float(getattr(val[0], val[1]))
                if np.isnan(val):
                    solverLog.error('Error: Undefined argument ' + token +' = ' + str(val) +' in function "' + self.string_formula + '"')
                    raise SystemExit
                stack.append(val)
            elif isinstance(token,tuple):
                val=float(getattr(token[0],token[1]))
                if np.isnan(val):
                    solverLog.error('Error: Undefined parameter ' + token +' = ' + str(val) +' in function "' + self.string_formula + '"')
                    raise SystemExit 
                stack.append(val)
            else:
                # if isinstance(token, str):
                #     val=self.str2parameter(token)
                #     if np.isnan(val):
                #         solverLog.error('Error: Undefined parameter '+token+' = '+str(val)+' in function "'+self.formula+'"')
                #         raise SystemExit 
                #     stack.append(val)
                # else:
                stack.append(token)
        return stack[0] # результат вычисления - единственный элемент в стеке
     
    #здесь заранее подготавливаем формулу в виде массива, где какие-то переменные на момент подготовки массива могут быть неизвестны, они будут известны потом в процессе расчета, на момент подготовки на эти переменные должны быть сохранены ссылки
    def prepare_formula(self,formula_string):
        LHS,RHS=formula_string.split('=',maxsplit=1) #разделяем строку с функцией на имя LHS и параметры и собственно саму формулу RHS
        _rez=re.search(r'([a-zA-Z0-9_]+)\({1}(.+)\){1}',LHS)
        name_of_function = _rez.group(1)
        string_with_arguments = _rez.group(2)
        for arg in string_with_arguments.split(','): #сохраняем имена аргументов, но пока не знаем их числовых значений
            self.ARGUMENTS[arg]=None
        self.shunting_yard(self.parse_string_to_generator(RHS)) #сохраняем формулу в виде польской нотации в self.polish_formula
        Parser_formula.USER_DEFINED_FUNCTIONS[name_of_function] = self #сохраняем готовую для расчета формулу в словарь класса
        return {name_of_function:self} #и возвращаем наружу на всякий случай

    def insert_values_in_arguments(self,**dict_of_values):
        for arg,value in dict_of_values.items():
            if arg in self.ARGUMENTS.keys():
                self.ARGUMENTS[arg]=self.str2link(value)
            else:
                solverLog.error(f'ERROR: unknown name of argument {arg} in attempt to insert value {value} in formula {self.string_formula}')

    def calculate(self):
        for key,value in self.ARGUMENTS.items():
            if value==None:
                solverLog.error(f'ERROR: unknown value for argument {key} in user defined formula {self.string_formula}')
                raise SystemExit
        return self._calc()

#как использовать парсер:
test_formula='function(x,y)=pt.N-(-pt.N_offtake)/(pt.Eff_mech_value+300+20)/1000+x/y'

нужно добавить возможность задавать в формулу имя другой формулы
добавить возможность использовать формулу задаваемую через точки


b=Parser_formula(a) #задаем через параметр a ссылку на базовые объект откуда будут извлекаться все параметры
b.prepare_formula(test_formula) #задаем строку с формулой
print(b.polish_formula)
b.insert_values_in_arguments(x=4,y='pt.test')
a.pt.test=2
print(b.polish_formula)
print(b.ARGUMENTS)
print(b.calculate()) #считаем формулу
a.pt.N=2000
print(b.polish_formula)
print(b.calculate())

