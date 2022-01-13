import config
import json, csv, pprint, time, xlsxwriter
import numpy as np
import pandas as pd

from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *

import talib
from talib import RSI, PLUS_DI, DX, CCI, ADX, ATR, MINUS_DI
from datetime import datetime
import bb
from bb import COCD, set_date, get_signal

""" client = Client(config.API_KEY, config.API_SECRET)



klines = client.get_historical_klines('SUSHIUSDT', Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")

data = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)
bb.set_date(data)
data = data[['Open','High','Low','Close','Volume']].copy()
dh = pd.read_csv('dh.csv')
dh = dh.set_index(dh['Unnamed: 0'],drop=True)
dh = dh.drop(['Unnamed: 0'],1)
dt = data.tail().copy()
dh = dh.append(dt)
dh.index = pd.to_datetime(dh.index)
dh = dh.sort_index(ascending=False)
dh.to_csv('dh.csv')
print(dh) """
class proccess:

    def __init__(self,df,symbol):
        self.open_price = float(df.iloc[3])
        self.rsi = float(df.iloc[5])
        self.pdi = float(df.iloc[6])
        self.ndi = float(df.iloc[7])
        self.adx = float(df.iloc[8])
        self.atr = float(df.iloc[9])
        self.date = df.name
        self.stop_loss = self.open_price - self.atr*2
        print('{}_{} : Proccess is opened'.format(self.date,symbol))
        df_open = pd.DataFrame([[self.date,self.open_price,self.stop_loss]],columns=['Open Time','Open Price','Stop Loss'])
        print(df_open)
        
    def close_proccess(self,success):
        rate = (self.current_price - self.open_price) / self.open_price
        df_close = pd.DataFrame([[self.date,self.current_date,self.open_price,self.current_price,rate,success]],columns=['Open Time','Close Time','Open Price','Close Price','Rate','Success'])
        print(df_close)

    
    def get_price_time(self,price,date):
        self.current_price = float(price)
        self.current_date = date
    
        
        
    def __del__(self):
        print('procces is closed')
            
    def check_stop_loss(self):
        if self.current_price <= self.stop_loss:
            success = False
            self.close_proccess(success)
            return True
        return False
        
    def check_dmi_pattern(self,pdi,ndi,adx):
            if pdi>ndi>adx:
                success = False
                if self.current_price >= self.open_price:
                    success = True
        
                self.close_proccess(success)
                return True
            return False
        
def check_proccess(transactions,pdi,ndi,adx,price,date):
    
    i = 0 
    while i < len(transactions):
        transactions[i].get_price_time(price,date)
        if transactions[i].check_dmi_pattern(pdi,ndi,adx):
            del transactions[i]  
        elif transactions[i].check_stop_loss():
            del transactions[i]  
        else:
            print('proccess still opend')
            i +=1
def stream(TRADE_SYMBOL):
    client = Client(config.API_KEY, config.API_SECRET)

    transactions = []

    klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")

    data = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)
    set_date(data)
    data = data[['Open','High','Low','Close','Volume']].copy()

    def process_message(msg):
        nonlocal data
        nonlocal transactions
        closes = np.empty(0)
        rsis = np.empty(0)
        if msg['e'] == 'error':
            print(msg['e'])
        else:
            candle = msg['k']
            is_closed = candle['x']
            
        
            if is_closed:
                
                close = candle['c']
                time_start = candle['t']
                open = candle['o']
                high = candle['h']
                low = candle['l']
                volume = candle['v']
                price = float(close)
                
                df = pd.DataFrame([[time_start,open,high,low,close,volume]],columns=['Open Time','Open','High','Low','Close','Volume'])  
                set_date(df)
                df = df.drop('Open Time', 1)
                

                data.loc[df.iloc[0].name] = df.iloc[0]

                data.sort_index(inplace=True)
                rsi = RSI(data['Close'])
                ndi = MINUS_DI(data['High'], data['Low'], data['Close'], timeperiod=14)
                pdi = PLUS_DI(data['High'], data['Low'], data['Close'], timeperiod=14)
                adx= ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
                atr = ATR(data['High'], data['Low'], data['Close'], timeperiod=14)
                datar = data.copy()
                datar['RSI']= rsi
                datar['DI+']= pdi
                datar['DI-']= ndi
                datar['ADX']= adx
                datar['ATR']= atr
                datar.dropna(inplace=True)
                datar.sort_index(ascending=False, inplace=True)
                COCD(datar)
                if transactions:
                    check_proccess(transactions,datar.iloc[0,6],datar.iloc[0,7],datar.iloc[0,8],price,datar.iloc[0].name)
        
                datar_grp = datar.groupby(['C'])
                if str(datar.iloc[0,10]) == 'GREEN':
                    signal = get_signal(datar_grp.get_group('GREEN'))
                else:
                    signal = get_signal(datar_grp.get_group('RED'))
                name = '{}_'.format(TRADE_SYMBOL)+str(datar.iloc[0].name)
                name = name.replace(":", "_")
                if not signal.empty:
                    transactions.append(proccess(datar.iloc[0],TRADE_SYMBOL))
                    #print('--- {} : Mismatch  ---'.format(TRADE_SYMBOL))
                    #print(signal)
                    signal.to_csv('D:/data/{}/{}.csv'.format(TRADE_SYMBOL,name))
                    signal.to_csv("G:/Drive'ım/data/{}/{}.csv".format(TRADE_SYMBOL,name))



                    
                    

                
            

    client = Client(config.API_KEY, config.API_SECRET)
    bm = BinanceSocketManager(client)
    conn_key = bm.start_kline_socket(TRADE_SYMBOL, process_message, interval=KLINE_INTERVAL_1MINUTE)

    bm.start()


stream('SUSHIUSDT')