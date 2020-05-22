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
import DataCollector

from Analyzer import Analyzer

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
    t = Trader(logger=logger, capital=capital, symbol=symbol, spt=spt)
    a = Analyzer(logger=logger, rh=rh)
    a.spline_fit(t, symbol=symbol, window_minutes=window_minutes, interval=interval)

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


    symbol = args.symbol
    window = args.window
    capital = args.capital
    spt = args.spt
    interval = args.interval

    try:
        rh = load_session()

    except InvalidCacheFile:
        rh = Robinhood(username="sangchoi93@gmail.com", password=getpass.getpass())
        rh.login()
        dump_session(rh) # so you don't have to do mfa again



    logging.info('symbol:{} window:{} capital:{} spt:{} interval:{}'.format(
        symbol, window, capital, spt, interval))

    analysis(rh, symbol=symbol, capital=capital, spt=spt, window_minutes=window, interval=interval)