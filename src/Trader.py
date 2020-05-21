import logging
import datetime
import enum
import pandas as pd

class TRANSACTION_TYPE:
    BUY = 'BUY'
    SELL = 'SELL'

class Trader:
    def __init__(self, logger, capital:float, symbol:str, spt:int=1):
        self.capital = capital
        self.symbol = symbol
        self.spt = spt
        self.transactions = 0
        self.num_buy = 0
        self.num_sell = 0
        self.stocks = 0
        self.last_price = 0
        self.logger = logger
        self.transaction_data = list()
    
    def _update_price(self, price:float):
        self.last_price = price
        
    def buy(self, price:float, amount:int = None):
        if not(amount):
            amount = self.spt

        self._update_price(price)

        if self.capital - price * amount < 0:
            self.logger.info('unable to buy')
        else:
            self.capital -= price * amount
            self.num_buy += 1
            self.stocks += amount
            self._update_price(price)
            self.transaction_data += [{
                'timestamp': datetime.datetime.now(),
                'symbol': self.symbol,
                'price': price,
                'action': TRANSACTION_TYPE.BUY
            }]
            self.logger.info('buy {} at {}'.format(self.spt, price))

    def sell(self, price:float, amount:int = None):
        if not(amount):
            amount = self.spt
       
        self._update_price(price)

        if self.stocks - amount < 0:
            self.logger.info('unable to sell')
        else:
            self.num_sell += 1
            self.capital += price * amount
            self.stocks -= amount
            self.transaction_data += [{
                'timestamp': datetime.datetime.now(),
                'symbol': self.symbol,
                'price': price,
                'action': TRANSACTION_TYPE.SELL
            }]
            self.logger.info('sell {} at {}'.format(self.spt, price))

    def store_log(self, filepath):
        df = pd.DataFrame(self.transaction_data).reset_index(drop=True)
        df.to_csv(filepath)

    def results(self):
        print('total transactions today: {}'.format(self.num_buy + self.num_sell))
        print('total bullet left: {}'.format(self.capital))
        print('total stocks left: {}'.format(self.stocks))
        print('stock asset value: {}'.format(self.stocks * self.last_price))
        print('total asset value: {}'.format(self.stocks * self.last_price + self.capital))

if __name__ == '__main__':
    print(TRANSACTION_TYPE.SELL)