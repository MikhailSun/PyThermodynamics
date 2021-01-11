from scipy.interpolate import interp1d
import logging


class UserFunction():
    @property
    def device(self):
        return self._device

    @property
    def params(self):
        return self._params

    @device.setter
    def device(self, val):
        self._device = val

    @params.setter
    def params(self, val):
        self._params = val

    def __init__(self, name, define, decl, params, type):
        self._device = None
        self._params = params
        self._name = name

        if type == 1:
            exec(f'from scipy.interpolate import interp1d\ndef {name}(x): return interp1d({decl})(x)', globals())
        if type == 2:
#            print(f'def {define}: return {decl}')
            exec(f'import numpy as np\ndef {define}: return {decl}', globals())
        if type == 3:
            exec(f'def {name}(x): return x', globals())

    def calculate(self):
        link = self._device
        if isinstance(self._params, list):
            vals = []
            for p in self._params:
                link = self._device
                if '-' in p:
                    _param = p.split('-')
                    for e in _param:
                        link = getattr(link, e)
                else:
                    link = getattr(link, p)

                vals.append(link)

            return globals()[self._name](vals)
        else:
            try:
                fl = float(self._params)
                return globals()[self._name](fl)
            except:
                pass

            if '-' in self._params:
                _param = self._params.split('-')
                for e in _param:
                    link = getattr(link, e)
            else:
                link = getattr(link, self._params)

            return globals()[self._name](link)

    def check_parameters(self, device):
        self._device = device
        
        
class udf():
    def __init__(self, link_to_engine, string_with_formula=''):
        self.link_to_engine=link_to_engine
            

