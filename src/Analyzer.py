import numpy as np
from sympy import Symbol
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers import solve

import time
import logging
import datetime
from scipy.interpolate import UnivariateSpline

from pyrh import Robinhood

from Trader import Trader
from DataCollector import DataCollector
import pandas as pd
import requests

class Analyzer:
    def __init__(self, logger, rh):
        self.logger = logger
        self.rh = rh
        self.collector = DataCollector(logger, rh)

    def spline_fit(self, t:Trader, symbol:str, window_minutes:int, interval:int):
        window = int(window_minutes * 60 / interval)
        trend = 'flat'
        l_data = list()
    
        while True:
            try:
                l_data += [self.collector.get_quote(symbol)]
                time.sleep(interval)
                
                if len(l_data) > window:
                    df_temp = pd.DataFrame(l_data[-1*window:])
                    x = df_temp.timestamp_sec.astype(float)
                    y = df_temp.price.astype(float)
                    cur_price = list(y)[-1]

                    y_spl = UnivariateSpline(x,y, k=4, s=2)
                    dx = y_spl.derivative()
                    roots = dx.roots()

                    if len(roots)>0:
                        d2x = y_spl.derivative(n=2)(roots)

                        if d2x[-1]>0:
                            if trend == 'up':
                                self.logger.debug('positive inflection, trigger buy at ' + str(cur_price))
                                t.buy(cur_price)
                            else:
                                self.logger.debug('positive inflection, setting up trend')
                                trend = 'up'
                        else:
                            if trend == 'down':                     
                                self.logger.debug('negative inflection, trigger sell at ' + str(cur_price))
                                t.sellall(cur_price)
                            else:
                                self.logger.debug('negative inflection, setting down trend')
                                trend = 'down'
                    else:
                        #No roots detected, we are likely in an up/down trend
                        if all(val<0 for val in dx(x[-3:])):
                            self.logger.debug('General downtrend detected, sell')
                            t.sellall(cur_price)

                        elif all(val>0 for val in dx(x[-3:])):
                            self.logger.debug('General uptrend detected, buy single stock')
                            t.buy(cur_price)

                    # grad1 = np.gradient(y)
                    # grad2 = np.gradient(grad1)            
                    # plt.plot(x, y, 'ro', ms=5)
                    # plt.plot(x,y_spl(x), 'g')
                    # plt.show()

            except KeyboardInterrupt as e:
                print(e)
                self.collector.convert_to_csv(symbol, l_data)
                t.store_log('data/{}_{}_transaction.csv'.format(symbol, datetime.date.today()))
                break
            
            except requests.exceptions.ReadTimeout as e:
                print(e)
                time.sleep(interval)
                continue


    def polynomial_fit(self, t:Trader, symbol:str, window_minutes:int, interval:int):
        # possible inflection coordinates
        window = int(window_minutes * 60 / interval)
        x_inf = list()
        y_inf = list()
        x_inf_put = list()
        y_inf_put = list()
        s = Symbol('x')
        l_data = list()
        prev = None
        
        while True:
            try:
                l_data += [self.collector.get_quote(self.rh, symbol)]
                time.sleep(interval)
                
                if len(l_data) > window:
                    df_temp = pd.DataFrame(l_data[-1*window:])
                    x = df_temp.timestamp_sec.astype(float)
                    y = df_temp.price.astype(float)

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
            
            except KeyboardInterrupt as e:
                print(e)
                self.collector.convert_to_csv(symbol, l_data)
                t.store_log('data/{}_{}_transaction.csv'.format(symbol, datetime.date.today()))
                break
            
            except requests.exceptions.ReadTimeout as e:
                print(e)
                time.sleep(interval)
                continue


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