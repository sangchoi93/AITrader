import numpy as np
from sympy import Symbol
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers import solve

import time
import logging

class CurveFitter:
    def __init__(self, logger):
        self.logger = logger
        pass


    def polynomial_fit(self, x:np.array, y:np.array):
        x_last = list(x)[-1]
        y_last = list(y)[-1]
        z = np.polyfit(x, y, 3)
        eq = eq_builder(z, 'x')
        sympy_exp = parse_expr(eq)

        # double derivative
        d = sympy_exp.diff(s).diff(s)
        result = solve(d,s)

        if len(result) == 1:
            l = d.evalf(subs={s: result[0]-0.5})
            r = d.evalf(subs={s: result[0]+0.5})
            if prev:
                # look for concavity changes
                if (prev >= 0 and r < 0) or (r >= 0 and prev < 0):
                    # only if inflection point exists within time window
                    if result[0] >= list(x)[0] and result[0] <= x_last:
                        if prev < 0 and r >= 0:
                            t.buy(y_last)
                            x_inf += [x_last]
                            y_inf += [y_last]
                        else:
                            t.sell(y_last)
                            x_inf_put += [x_last]
                            y_inf_put += [y_last]

                        t._update_price(y_last)
                        t.results()

                        # f = np.poly1d(z)
                        # y_fit = f(x)
                        # inflection_point = sympy_exp.evalf(subs={s: result[0]})
                        # plt.plot(x, y, '-', x, y_fit, 'b-', result[0], inflection_point, 'rx', \
                        #          x_last, y_last, 'go')
                        # plt.show()
                        prev = r
            else:
                prev = r
        else:
            print('unsolvable?', result)

    def spline_fit(self):
        pass

def eq_builder(a: np.array, var='s'):
    length = len(a)
    eq = ''
    for i, coef in enumerate(a):
#         print(i, coef)
        if i != 0 and str(coef)[0] != '-':
            eq += '+'
        if i != length-1:
            eq += str(coef) + '*{}**{}'.format(var, str(length-i-1))
            
        else:
            eq += str(coef)
        
    return eq