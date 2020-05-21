import pandas as pd
import os,sys
import numpy as np
import datetime, time

import logging

from pyrh import Robinhood, dump_session, load_session
from pyrh.exceptions import InvalidCacheFile

import getpass
import requests
import argparse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def get_quote(rh, symbol):
    time_now = datetime.datetime.now()
    d = datetime.date.today()
    d_today = datetime.datetime(d.year, d.month, d.day)
    quote = rh.quote_data(symbol)

    d = {
        'symbol': symbol,
        'timestamp':time_now.isoformat(),
        'timestamp_sec':(time_now - d_today).total_seconds(),
        'price':quote['last_trade_price']
    }
    
    return d

def convert_to_csv(symbol:str, l_data:list, prefix:str=None, suffix:str=None, filename:str=None):
    if l_data:
        # formulate filename if filename not provided
        if not(filename):
            filename = 'data/'
            if prefix:
                filename = filename + prefix + '_'
            filename = filename + '{}_{}.csv'.format(datetime.date.today(), symbol)
            if suffix:
                filename = filename + '_' + suffix

        if os.path.isfile(filename):
            df_tmp = pd.read_csv(filename).set_index('timestamp_sec')
            if len(df_tmp) != 0:
                df = df_tmp.append(pd.DataFrame(l_data).set_index('timestamp_sec'))
        else:
            df = pd.DataFrame(l_data).set_index('timestamp_sec')
        
        df.to_csv(filename)
        print('df saved {} to {}'.format(len(df), filename))

    else:
        print('l_data empty!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--symbol", help="ticker symbol of the stock", type=str)
    parser.add_argument("-i", "--interval", help="datapoint interval in seconds", type=int, default=1)
    args = parser.parse_args()

    l_data = list()
    df = pd.DataFrame()
    symbol = args.symbol
    SLEEP_TIME = args.interval
    # Log in to app (will prompt for two-factor)

    try:
        rh = load_session()
    except InvalidCacheFile:
        rh = Robinhood(username="sangchoi93@gmail.com", password=getpass.getpass())
        rh.login()
        dump_session(rh) # so you don't have to do mfa again

    while True:
        try:
            l_data += [get_quote(rh, symbol)]
            time.sleep(SLEEP_TIME)
            if len(l_data)%100 == 0:
                convert_to_csv(symbol, l_data, 'dc')
                l_data = list()
        
        except requests.exceptions.ReadTimeout as e:
            print(e)
            time.sleep(SLEEP_TIME)
            continue

        except KeyboardInterrupt as e:
            convert_to_csv(symbol, l_data, 'dc')
            break
