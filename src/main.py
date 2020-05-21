import pandas as pd
import os,sys
import numpy as np

import matplotlib.pyplot as plt
import datetime

from sympy import Symbol
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers import solve

import time
import logging

from pyrh import Robinhood, dump_session, load_session
from pyrh.exceptions import InvalidCacheFile
import getpass

from Trader import Trader
import requests
import data_collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

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

def analysis(rh:Robinhood, symbol:str, capital:float, spt:int, window_minutes:int, interval:int):
    l_data = list()
    window = int(window_minutes * 60 / interval)

    while len(l_data) <= window:
        l_data += [data_collector.get_quote(rh, symbol)]
        time.sleep(interval)

    logger.info('enough datapoints: starting analyzing... {}'.format(len(l_data)))

    t = Trader(logger, capital, symbol, spt)
    # possible inflection coordinates
    x_inf = list()
    y_inf = list()
    x_inf_put = list()
    y_inf_put = list()
    s = Symbol('x')

    prev = None

    while True:
        try:
            l_data += [data_collector.get_quote(rh, symbol)]
            time.sleep(interval)
            
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
            else:
                print('unsolvable?', result)
        
        except KeyboardInterrupt as e:
            print(e)
            data_collector.convert_to_csv(symbol, l_data)
            t.store_log('data/trans_{}_{}.csv'.format(symbol, datetime.date.today()))
            break
        
        except requests.exceptions.ReadTimeout as e:
            print(e)
            time.sleep(interval)
            continue


# Log in to app (will prompt for two-factor)

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--symbol", help="ticker symbol of the stock", type=str)
    parser.add_argument("-t", "--spt", help="how many stocks to buy/sell per transaction", type=int)
    parser.add_argument("-c", "--capital", help="starting capital", type=int)
    parser.add_argument("-w", "--window", help="moving window in minutes", type=int)
    parser.add_argument("-i", "--interval", help="datapoint interval in seconds", type=int, default=1)
    args = parser.parse_args()

    try:
        rh = load_session()
    except InvalidCacheFile:
        rh = Robinhood(username="sangchoi93@gmail.com", password=getpass.getpass())
        rh.login()
        dump_session(rh) # so you don't have to do mfa again

    symbol = args.symbol
    window = args.window
    capital = args.capital
    spt = args.spt
    interval = args.interval

    logging.info('symbol:{} window:{} capital:{} spt:{} interval:{}'.format(
        symbol, window, capital, spt, interval))

    analysis(rh, symbol=symbol, capital=capital, spt=spt, window_minutes=window, interval=interval)