import bb.config as config
import json, csv, pprint, time, xlsxwriter
import numpy as np
import pandas as pd

from datetime import datetime
from binance.client import Client
from talib import RSI, PLUS_DI, DX, CCI, ADX
from binance.websockets import BinanceSocketManager
from binance.enums import *
import bb

import talib

from bb import stream


stream(config.BTC)
stream(config.SUSHI)


""" def stream(TRADE_SYMBOL):
    client = Client(config.API_KEY, config.API_SECRET)



    klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")

    data = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)
    bb.set_date(data)
    data = data[['Open','High','Low','Close','Volume']].copy()

    def process_message(msg):
        nonlocal data
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
                
                df = pd.DataFrame([[time_start,open,high,low,close]],columns=['Open Time','Open','High','Low','Close'])  
                bb.set_date(df)
                df = df.drop('Open Time', 1)

                data.loc[df.iloc[0].name] = df.iloc[0]

                data.sort_index(inplace=True)
                rsi = talib.RSI(data['Close'])
                datar = data.copy()
                datar['RSI']= rsi
                datar.dropna(inplace=True)
                datar.sort_index(ascending=False, inplace=True)
                bb.COCD(datar)
                datar_grp = datar.groupby(['C'])
                if str(datar.iloc[0,6]) == 'GREEN':
                    signal = bb.get_signal(datar_grp.get_group('GREEN'))
                else:
                    signal = bb.get_signal(datar_grp.get_group('RED'))
                name = '{}_'.format(TRADE_SYMBOL)+str(datar.iloc[0].name)
                name = name.replace(":", "_")
                print(signal)
                signal.to_csv('D:/data/{}/{}.csv'.format(TRADE_SYMBOL,name))


                    
                    

                
            

    client = Client(config.API_KEY, config.API_SECRET)
    bm = BinanceSocketManager(client)
    conn_key = bm.start_kline_socket(TRADE_SYMBOL, process_message, interval=KLINE_INTERVAL_1MINUTE)

    bm.start()
 """