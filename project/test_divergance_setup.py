import config
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

client = Client(config.API_KEY, config.API_SECRET)



klines = client.get_historical_klines("SUSHIUSDT", Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")

color = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)

def set_date(df):
    date = df['Open Time']
    final_date = []
    for time in date.unique():
        time = time/1000
        readable = datetime.utcfromtimestamp(time)
        final_date.append(readable) 
    df.set_index(pd.DatetimeIndex(final_date), inplace=True)

set_date(color)
rsi = talib.RSI(color['Close'],14)
color['RSI'] = rsi
color.dropna(inplace=True)
color = color[['Open','High','Low','Close','Volume','RSI']]
color.sort_index(ascending=False, inplace=True)

def COCD(df):
    color= []
    for i in range(len(df)):
            
        if float(df.iloc[i,0]) > float(df.iloc[i,3]):
            color.append('RED')
        else:
            color.append('GREEN')
    df['C'] = color

    
COCD(color)

color_grp = color.groupby('C')

def get_signal(df):
    date = str(df.iloc[0].name)
    signals= pd.DataFrame(columns=[date,'Close>','RSI>','Close','RSI'])
    
    close = float(df.iloc[0,3])
    rsi = float(df.iloc[0,5])
    for i in range(1,(len(df))):
        if close > float(df.iloc[i,3]):
            isBTC  = True
        else:
            isBTC = False
            
        if rsi > float(df.iloc[i,5]):
            isBTR  = True
        else:
            isBTR = False
        
        if isBTC != isBTR:
            signals = signals.append({date:df.iloc[i].name,'Close>':isBTC,'RSI>':isBTR,'Close':df.iloc[i,3],'RSI':df.iloc[i,5]},ignore_index=True)
    
    
    signals = signals.set_index(signals[date]).drop(date, 1 )
    
    return signals

if str(color.iloc[0,6]) == 'GREEN':
    print('GREEN')
    print('-----')
    signal = get_signal(color_grp.get_group('GREEN'))
else:
    signal = get_signal(color_grp.get_group('RED'))
    print('RED')
    print('-----')
print(signal)
name = 'sushi_'+str(color.iloc[0].name)
name = name.replace(":", "_")
signal.to_csv('./{}.csv'.format(name))