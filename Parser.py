# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 10:55:11 2020

@author: Sundukov
"""




import ast
import numpy as np
import logging
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

# a=test1()
# a.pt=test2()
# a.pt.nnn=test2()
# a.devices['pt']=a.pt
# a.devices['air_bleed_out']=a.air_bleed_out
# a.pt.N=1000
# a.pt.N_offtake=2000
# a.pt.Eff_mech_value=0.95

# test_formula='-pt.N-pt.N_offtake/(-pt.Eff_mech_value+300+20)/1000'
# # stro='air_bleed_out[0][G_abs_from]'
# # stro='deg(arctan(1))'
# p = Parser(a)
# ee=p.parse(test_formula)
# e=p.calculate()

# print(e)
# print(type(e))
# Expr(value=BinOp(left=Attribute(value=Name(id='pt', ctx=Load()), attr='N', ctx=Load()), op=Sub(), right=BinOp(left=BinOp(left=Attribute(value=Name(id='pt', ctx=Load()), attr='N_offtake', ctx=Load()), op=Div(), right=Attribute(value=Name(id='pt', ctx=Load()), attr='Eff_mech_value', ctx=Load())), op=Div(), right=Num(n=1000))))

class Parser_formula():
    def __init__(self,link_to_extract=False):
        self.link_to_extract=link_to_extract
        self.formula=np.nan
        if self.link_to_extract==False:
            solverLog.error('ERROR: Parser_formula did not get link_to_extract')
            raise SystemExit 
        self.OPERATORS = {'+': (1, lambda x, y: x + y),
                          '-': (1, lambda x, y: x - y),
                          '*': (2, lambda x, y: x * y),
                          '/': (2, lambda x, y: x / y),
                          '^': (3, lambda x, y: x ** y)
                          }
        self.FUNCTIONS = {'sqrt': lambda x: np.sqrt(x),
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
        self.polish_formula=[]
    #Генератор, получает на вход строку, возвращает числа в формате float, операторы и скобки в формате символов или ссылки на переменные.
    def parse_string(self,formula_string):
        self.formula=formula_string
        number = ''
        string_parameter=''
        for s in formula_string:
            if s in '1234567890.' and not string_parameter: # если символ - цифра или точка и строка пустая, то собираем число
                # print('111')
                number += s
                continue
            elif number: # если символ не цифра, то выдаём собранное число и начинаем собирать заново
                # print('111a')
                yield float(number) 
                number = ''
            if (s.isalnum() or s in '_.') and not number:# если символ - буква или точка и число пустое, то собираем из нее имя параметра или имя оператора, дальше нужно распознать параметр это или оператор
                # print('222')
                string_parameter+=s
                continue
            elif string_parameter: #здксь обнаружили, что строка закончилась и нужно определить что в ней: сслыка на параметр или оператор
                # print('222a')
                yield string_parameter
                string_parameter=''
            if s in self.OPERATORS or s in "()": # если символ - оператор или скобка, то выдаём как есть
                yield s
            else:
                solverLog.error('Forbidden symbol in formula '+str(s))
        if number:  # если в конце строки есть число, выдаём его
            yield float(number)
        if string_parameter:
            yield string_parameter
    #Генератор, получает на вход итерируемый объект из чисел и операторов в инфиксной нотации, возвращает числа и операторов в обратной польской записи.            
    def shunting_yard(self,parsed_formula):
        stack = []  # в качестве основного стэка используем список
        self.polish_formula = [] #тут будет хранить итоговую формулу в польской нотации для вычисления (в виде массива)
        for token in parsed_formula:
            # print(token)
            # если элемент - оператор, то отправляем дальше все операторы из стека, 
            # чей приоритет больше или равен пришедшему,
            # до открывающей скобки или опустошения стека.
            # здесь мы пользуемся тем, что все операторы право-ассоциативны
            if token in self.OPERATORS: 
                while stack and stack[-1] != "(" and ((stack[-1] in self.OPERATORS and self.OPERATORS[token][0] <= self.OPERATORS[stack[-1]][0]) or (stack[-1] in self.FUNCTIONS)):
                    self.polish_formula.append(stack.pop())
                    #elif stack[-1] in self.USER_FUNCTIONS TODO! тут надо будет предусмотреть возможность использования в формуле пользовательских функций, формируемых как раз за счет этого же парсера
                stack.append(token)
            elif token in self.FUNCTIONS:
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
        rez=self.link_to_extract
        for val in broken_string:
            if hasattr(rez,val):
                rez=getattr(rez,val)
            else:
                return 'unknown parameter '+string
        return rez  
    def str2link(self,string): #вспомогательная функция для преобразования строки, содержащей ссылку на параметр в tuple, где первое значение хранит указатель на объект, а второе значение - имя параметры этого объекта, значение которого нужно узнать. Так странно сделано из-за того, что в питоне есть mutable и immutable переменные
        rez=self.link_to_extract
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

            if token in self.OPERATORS:  # если приходящий элемент - оператор,
                y, x = stack.pop(), stack.pop()  # забираем 2 числа из стека
                # print(y,x)
                stack.append(self.OPERATORS[token][1](x, y)) # вычисляем оператор, возвращаем в стек
            elif token in self.FUNCTIONS:
                x=stack.pop()
                stack.append(self.FUNCTIONS[token](x))
            elif isinstance(token,tuple):
                val=getattr(token[0],token[1])
                if np.isnan(val):
                    solverLog.error('Error: Undefined parameter '+token+' = '+str(val)+' in function "'+self.formula+'"')
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
        _temp=self.parse_string(formula_string)
        self.shunting_yard(_temp)
    
    def calculate(self):
        return self._calc()

#как использовать парсер:
# b=Parser_formula(a) #задаем через параметр ссылку на объект откуда будут извлекаться все параметры
# b.prepare_formula(test_formula) #задаем строку с формулой
# print(b.polish_formula)
# print(b.calculate()) #считаем формулу
# a.pt.N=2000
# print(b.polish_formula)
# print(b.calculate())

