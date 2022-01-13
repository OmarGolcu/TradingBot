import config
import json, csv, pprint, time, xlsxwriter
import numpy as np
import pandas as pd

from binance.client import Client
from binance import BinanceSocketManager
from binance.enums import *

import talib
from talib import RSI, PLUS_DI, DX, CCI, ADX, MINUS_DI,ATR, SAR
from datetime import datetime

RSI_PERIOD = config.RSI_PERIOD
TRADE_SYMBOL = config.TRADE_SYMBOL


# color of candles with numpy array
def COC(candles):
    green = []
    red = []
    for candle in candles:
        open = float(candle[1])
        close = float(candle[4])
        if open > close :
            red.append(candle)
        else:
            green.append(candle)
    coc = np.array([green,red])
    return coc


# add color in array
def COCN(candles):
    for candle in candles:
        if float(candle[1]) > float(candle[4]):
            candle.append('RED')
        else:
            candle.append('GREEN')

    return candles

# add color in dictionary
def COCD(df):
    color= []
    for i in range(len(df)):

        if float(df.iloc[i,0]) > float(df.iloc[i,3]):
            color.append('RED')
        else:
            color.append('GREEN')
    df['C'] = color


'''def COCD(candles):
    for candle in candles:
        if float(candle['Open']) > float(candle['Close']):
            candle['C'] ='RED'
        else:
            candle['C'] = 'GREEN'

    return candles '''

# nice try for writing xlsx
def excel_file_writer(name,candle):
    workbook = xlsxwriter.Workbook('{}.xlsx'.format(name))
    worksheet = workbook.add_worksheet()
    row = 0
    for col,data in enumerate(candle):
        worksheet.write_column(row,col,data)
    workbook.close()


# dataframe to xlsx

def efw_df(name,candle):
    df = pd.DataFrame(candle, columns = ['Close>','RSI>','Close','RSI'])
    
    writer = pd.ExcelWriter('{}.xlsx'.format(name), engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()



def stream_candle():
   

    def process_message(msg):
        closes = np.empty(0)
        rsis = np.empty(0)
        if msg['e'] == 'error':
            print(msg['e'])
        else:
            candle = msg['k']
            is_closed = candle['x']
            close = candle['c']

            if is_closed:
                closes = np.append(closes, float(close)) 
                
                if len(closes)>RSI_PERIOD:
                    rsi = talib.RSI(closes,RSI_PERIOD)
                    rsi_last = rsi[-1]
                    rsis = np.append(rsis, float(rsi_last)) 
        

            
        print('CLOSES :{}'.format(closes))
        print('RSI :{}'.format(rsis))
        pprint.pprint(candle)

    client = Client(config.API_KEY, config.API_SECRET)
    bm = BinanceSocketManager(client)
    conn_key = bm.start_kline_socket(TRADE_SYMBOL, process_message, interval=KLINE_INTERVAL_15MINUTE)

    bm.start()


#get open, high, low ,close column from historical data
def get_ohlc_his(klines):
    open = np.empty(0)
    high = np.empty(0)
    low = np.empty(0)
    close = np.empty(0)
    for kline in klines:
        open = np.append(open, float(kline[1]))
        high = np.append(high, float(kline[2]))
        low = np.append(low, float(kline[3]))
        close = np.append(close, float(kline[4])) 
    return np.array([open,high,low,close])



def isSupportRSI(df,i):
    support = df['RSI'][i] < df['RSI'][i-1]  and df['RSI'][i] < df['RSI'][i+1] \
    and df['RSI'][i+1] < df['RSI'][i+2] and df['RSI'][i-1] < df['RSI'][i-2]

    return support

def isResistanceRSI(df,i):
    resistance = df['RSI'][i] > df['RSI'][i-1]  and df['RSI'][i] > df['RSI'][i+1] \
and df['RSI'][i+1] > df['RSI'][i+2] and df['RSI'][i-1] > df['RSI'][i-2] 

    return resistance

def isSupport(df,i):
    support = df['Low'][i] < df['Low'][i-1]  and df['Low'][i] < df['Low'][i+1] \
    and df['Low'][i+1] < df['Low'][i+2] and df['Low'][i-1] < df['Low'][i-2]

    return support

def isResistance(df,i):
    resistance = df['High'][i] > df['High'][i-1]  and df['High'][i] > df['High'][i+1] \
    and df['High'][i+1] > df['High'][i+2] and df['High'][i-1] > df['High'][i-2] 

    return resistance

def rsi_sup(df):
    sup = []
    for i in range(2,df.shape[0]-2):
        if isSupportRSI(df,i):
            sup.append((df.index[i],df['RSI'][i]))
    sup_df = pd.DataFrame(sup,columns=['Date','RSI_SUP']).set_index('Date')
    return sup_df
def rsi_res(df):
    res = []
    for i in range(2,df.shape[0]-2):
        if isResistanceRSI(df,i):
            res.append((df.index[i],df['RSI'][i]))
    res_df = pd.DataFrame(res,columns=['Date','RSI_RES']).set_index('Date')
    return res_df

def candle_sup(df):
    sup = []
    for i in range(2,df.shape[0]-2):
        if isSupport(df,i):
            sup.append((df.index[i],df['Low'][i]))
    sup_df = pd.DataFrame(sup,columns=['Date','CANDLE_SUP']).set_index('Date')
    return sup_df

def candle_res(df):
    res = []
    for i in range(2,df.shape[0]-2):
        if isResistance(df,i):
            res.append((df.index[i],df['High'][i]))
    res_df = pd.DataFrame(res,columns=['Date','CANDLE_RES']).set_index('Date')
    return res_df



def positive_mismatch(ohlcr):
    positive_mismatch = False
    rsi_supp = rsi_sup(ohlcr)
    
    rsi_sup_first = float(rsi_supp.iloc[0].values)

    rsi_sup_last = float(rsi_supp.iloc[-1].values)

    rsi_direction = rsi_sup_first - rsi_sup_last
    if rsi_direction > 0 :
        rsi_dir = 'negatif'
    else :
        rsi_dir = 'pozitif'
        
    candle_supp = candle_sup(ohlcr)

    candle_sup_first = float(candle_supp.iloc[0].values)

    candle_sup_last = float(candle_supp.iloc[-1].values)

    candle_direction = candle_sup_first - candle_sup_last
    if candle_direction > 0 :
        candle_dir = 'negatif'
    else:
        candle_dir = 'poizitif'
        
    if rsi_dir != candle_dir:
        positive_mismatch = True
        return [positive_mismatch,ohlcr.index[0],ohlcr.index[-1]]
    else:
        return positive_mismatch
    
def split_seq(seq, num_pieces):
    start = 0
    for i in range(num_pieces):
        stop = start + len(seq[i::num_pieces])
        yield seq[start:stop]
        start = stop

def set_date(df):
    date = df['Open Time']
    final_date = []
    for time in date.unique():
        time = time/1000
        readable = datetime.utcfromtimestamp(time)
        final_date.append(readable) 
    df.set_index(pd.DatetimeIndex(final_date), inplace=True)

def set_opentime(df):
    date = df['Open Time']
    final_date = []
    for time in date:
        time = float(time)/1000
        readable = datetime.utcfromtimestamp(time)
        final_date.append(readable) 
    df['Open Time'] = final_date

def set_endtime(df):
    date = df['End Time']
    final_date = []
    for time in date:
        time = float(time)/1000
        readable = datetime.utcfromtimestamp(time)
        final_date.append(readable) 
    df['End Time'] = final_date


def get_signal(df):
    date = str(df.iloc[0].name)
    signals= pd.DataFrame(columns=[date,'Close>','RSI>','Close','RSI','DI+','DI-','ADX','ATR'])


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
            signals = signals.append({date:df.iloc[i].name,'Close>':isBTC,'RSI>':isBTR,'Close':df.iloc[i,3],'RSI':df.iloc[i,5],'DI+':df.iloc[i,6],'DI-':df.iloc[i,7],'ADX':df.iloc[i,8],'ATR':df.iloc[i,9]},ignore_index=True)


    signals = signals.set_index(signals[date]).drop(date, 1 )
    return signals


def dmi_pattern_long(current_data,signals,rsi_sups):

    c_ndi = float(current_data.iloc[7])
    c_adx = float(current_data.iloc[8])
    c_pdi = float(current_data.iloc[6])
    if c_ndi > c_adx > c_pdi:
        for date, row in signals.T.iteritems():
            ndi = row['DI-']
            adx = row['ADX']
            pdi = row['DI+']
            if not ndi > adx > pdi:
                signals = signals.drop(date)
            elif not date in rsi_sups:
                signals = signals.drop(date)
        return signals
    else:
        signals = pd.DataFrame()
        return signals

def dmi_pattern_short(current_data,signals,rsi_res):

    c_ndi = float(current_data.iloc[7])
    c_adx = float(current_data.iloc[8])
    c_pdi = float(current_data.iloc[6])
    if c_pdi > c_adx > c_ndi:
        for date, row in signals.T.iteritems():
            ndi = row['DI-']
            adx = row['ADX']
            pdi = row['DI+']
            if not pdi > adx > ndi:
                signals = signals.drop(date)
            elif not date in rsi_res:
                signals = signals.drop(date)
        return signals
    else:
        signals = pd.DataFrame()
        return signals

def isSupR(df,i):
    support = df['RSI'][i] < df['RSI'][i-1]  and df['RSI'][i] < df['RSI'][i+1] 
    return support

def isResR(df,i):
    res = df['RSI'][i] > df['RSI'][i-1]  and df['RSI'][i] > df['RSI'][i+1] 
    return res

def r_sup(df):
    rsis = []
    for i in range(1,df.shape[0]-1):
        if isSupR(df,i):
            rsis.append((df.iloc[i].name))
    return rsis

def r_res(df):
    rsis = []
    for i in range(1,df.shape[0]-1):
        if isResR(df,i):
            rsis.append((df.iloc[i].name))
    return rsis


# Long divergence setup
def streamL(TRADE_SYMBOL):
    client = Client(config.API_KEY, config.API_SECRET)



    klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")

    data = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)
    set_date(data)
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
                volume = candle['v']
                
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
                rsi_sups = r_sup(datar)
        
                datar_grp = datar.groupby(['C'])
                if str(datar.iloc[0,10]) == 'RED':
                    signal = get_signal(datar_grp.get_group('RED'))
                    name = '{}_'.format(TRADE_SYMBOL)+str(datar.iloc[0].name)
                    name = name.replace(":", "_")
                    if not signal.empty:
                        result = dmi_pattern_long(datar.iloc[0],signal,rsi_sups)
                        if not result.empty:
                            print(' {} :  Long Position '.format(TRADE_SYMBOL))
                            print(result)
                       # else:

                            #print('--- {} : No Setup  ---'.format(TRADE_SYMBOL))
                #else:
                    #print('--- {} : No Setup  ---'.format(TRADE_SYMBOL))
                    #signal.to_csv('D:/data/{}/{}.csv'.format(TRADE_SYMBOL,name))
                    #signal.to_csv("G:/Drive'ım/data/{}/{}.csv".format(TRADE_SYMBOL,name))


                    
                    

                
            

    client = Client(config.API_KEY, config.API_SECRET)
    bm = BinanceSocketManager(client)
    conn_key = bm.start_kline_socket(TRADE_SYMBOL, process_message, interval=KLINE_INTERVAL_5MINUTE)

    bm.start()
# short divergence setup
def streamS(TRADE_SYMBOL):
    client = Client(config.API_KEY, config.API_SECRET)



    klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")

    data = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)
    set_date(data)
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
                volume = candle['v']
                
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
                rsi_res = r_res(datar)
        
                datar_grp = datar.groupby(['C'])
                if str(datar.iloc[0,10]) == 'GREEN':
                    signal = get_signal(datar_grp.get_group('GREEN'))
                    name = '{}_'.format(TRADE_SYMBOL)+str(datar.iloc[0].name)
                    name = name.replace(":", "_")
                    if not signal.empty:
                        result = dmi_pattern_short(datar.iloc[0],signal,rsi_res)
                        if not result.empty:
                            print(' {} :  Short Position '.format(TRADE_SYMBOL))
                            print(result)
                       # else:

                            #print('--- {} : No Setup  ---'.format(TRADE_SYMBOL))
                #else:
                    #print('--- {} : No Setup  ---'.format(TRADE_SYMBOL))
                    #signal.to_csv('D:/data/{}/{}.csv'.format(TRADE_SYMBOL,name))
                    #signal.to_csv("G:/Drive'ım/data/{}/{}.csv".format(TRADE_SYMBOL,name))


                    
                    

                
            

    client = Client(config.API_KEY, config.API_SECRET)
    bm = BinanceSocketManager(client)
    conn_key = bm.start_kline_socket(TRADE_SYMBOL, process_message, interval=KLINE_INTERVAL_15MINUTE)

    bm.start()


def stream(TRADE_SYMBOL):
    client = Client(config.API_KEY, config.API_SECRET)



    klines = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")

    data = pd.DataFrame(klines, columns=config.FIELD_HISTORICAL)
    set_date(data)
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
                volume = candle['v']
                
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
                
        
                datar_grp = datar.groupby(['C'])
                if str(datar.iloc[0,10]) == 'RED':
                    global short_positions
                    rsi_sups = r_sup(datar)
                    signal = get_signal(datar_grp.get_group('RED'))
                    name = '{}_'.format(TRADE_SYMBOL)+str(datar.iloc[0].name)
                    name = name.replace(":", "_")
                    if not signal.empty:
                        result = dmi_pattern_long(datar.iloc[0],signal,rsi_sups)
                        if not result.empty:
                            print(' {} :  Long Position '.format(TRADE_SYMBOL))
                            print(result)
                       # else:

                            #print('--- {} : No Setup  ---'.format(TRADE_SYMBOL))
                else:
                    global short_positions
                    rsi_res = rsi_res(datar)
                    signal = get_signal(datar_grp.get_group('GREEN'))
                    name = '{}_'.format(TRADE_SYMBOL)+str(datar.iloc[0].name)
                    name = name.replace(":", "_")
                    if not signal.empty:
                        result = dmi_pattern_short(datar.iloc[0],signal,rsi_res)
                        if not result.empty:
                            print(' {} :  Short Position '.format(TRADE_SYMBOL))
                            print(result)
                    #print('--- {} : No Setup  ---'.format(TRADE_SYMBOL))
                    #signal.to_csv('D:/data/{}/{}.csv'.format(TRADE_SYMBOL,name))
                    #signal.to_csv("G:/Drive'ım/data/{}/{}.csv".format(TRADE_SYMBOL,name))


                    
                    

                
            

    client = Client(config.API_KEY, config.API_SECRET)
    bm = BinanceSocketManager(client)
    conn_key = bm.start_kline_socket(TRADE_SYMBOL, process_message, interval=KLINE_INTERVAL_15MINUTE)

    bm.start()

# backtest for candlestick pattern
def candlestick_backtest(SYMBOL='',CANDLE_TIMEZONE='',RSI_TIMEZONE='',START_DATE='',END_DATE='',):
    client = Client(config.API_KEY, config.API_SECRET)
    interval = {
        '1m' : Client.KLINE_INTERVAL_1MINUTE ,
        '3m' : Client.KLINE_INTERVAL_3MINUTE ,
        '5m' : Client.KLINE_INTERVAL_5MINUTE ,
        '15m': Client.KLINE_INTERVAL_15MINUTE ,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
    }
    SEARCH_RATE=840000
    if RSI_TIMEZONE == '15m' and CANDLE_TIMEZONE =='1m':
        SEARCH_RATE = 840000
    if RSI_TIMEZONE == '15m' and CANDLE_TIMEZONE =='3m':
        SEARCH_RATE = 840000
    if RSI_TIMEZONE == '5m' and CANDLE_TIMEZONE =='1m':
        SEARCH_RATE = 240000
    if RSI_TIMEZONE == '5m' and CANDLE_TIMEZONE =='3m':
        SEARCH_RATE = 240000
    if END_DATE == '':
        candle_data = client.get_historical_klines(SYMBOL, interval[CANDLE_TIMEZONE],START_DATE)
        rsi_data = client.get_historical_klines(SYMBOL, interval[RSI_TIMEZONE],START_DATE)
    else:
        candle_data = client.get_historical_klines(SYMBOL, interval[CANDLE_TIMEZONE],START_DATE,END_DATE)
        rsi_data = client.get_historical_klines(SYMBOL, interval[RSI_TIMEZONE],START_DATE,END_DATE)
    
    
        
    
    df_candle = pd.DataFrame(candle_data, columns=config.FIELD_HISTORICAL)
    df_rsi = pd.DataFrame(rsi_data, columns=config.FIELD_HISTORICAL)
    set_date(df_candle)
    set_date(df_rsi)
    df_candle = df_candle.copy().iloc[:,:7]
    df_rsi = df_rsi.copy().iloc[:,:7]
    
    psar_candle = SAR(df_candle['High'],df_candle['Low'])
    rsi = RSI(df_rsi['Close'])
    
    
    df_candle['PSAR'] = psar_candle
    df_candle.dropna(inplace=True)
    
    df_rsi['RSI'] = rsi
    df_rsi.dropna(inplace=True)
    
    permisson = False
    res = []
    trades = pd.DataFrame()
    df_candle['PSAR'] = df_candle['PSAR'].astype(str)
    for index, row in df_rsi.iterrows():
        
        if not trades.empty:
            trades_status = trades.groupby(['Status'])
        #trades_status.get_group('Close')
        if row['RSI'] > 50 : 
            permisson  = True
            time = row['Close Time']+1
            search_df = df_candle.loc[(df_candle['Open Time' ] >= time ) & (df_candle['Open Time'] <= time+SEARCH_RATE)]
            positions = search_df[(search_df['Open'] == search_df['High']) & (search_df['Close'] > search_df['Low'] ) & (search_df['PSAR'] > search_df['Close'] )]
            positions.insert(8,'Status', 'Open')
            positions.insert(9,'Margin', 100)
            positions.insert(10,'End Time', '')
            positions['Close Price'] = np.nan
            positions['Ratio'] = np.nan
            positions.insert(13,'PNL', '')
            positions['PNLQ'] = np.nan
            positions
            trades = trades.append(positions)


            if not trades.empty:
                trades_status = trades.groupby(['Status'])
                try:
                    if not trades_status.get_group('Open').empty:
                        for ind, ro in trades_status.get_group('Open').iterrows():
                            match_df = search_df.loc[(search_df['Open Time'] > ro['Open Time'])]
                            for i,r in match_df.iterrows():
                                if ro['PSAR'] <= r['High']:
                                    trades.at[ind,'End Time'] = r['Open Time']
                                    trades.at[ind,'Close Price'] = ro['PSAR']
                                    trades.at[ind,'Ratio'] = float(ro['PSAR'])/float(ro['Close'])
                                    trades.at[ind,'PNL'] = 'Profit'
                                    trades.at[ind,'PNLQ'] = ((float(ro['PSAR'])/float(ro['Close']))*100) - 100
                                    trades.at[ind,'Status'] = 'Close'
                                    break
                            '''
                            ro['End Time'] = r['Open Time']
                            ro['Close Price'] = ro['Psar']
                            ro['Ratio'] = float(ro['Psar'])/float(ro['Close'])
                            ro['PNL'] = 'Profit'
                            ro['PNLQ'] = ((float(ro['Psar'])/float(ro['Close']))*100) - 100
                            ro['Status'] = 'Close'
                            '''
                except:
                    print('All Position is closed')



        else:
            permission = False
            if not trades.empty:
                trades_status = trades.groupby(['Status'])
                try:
                    if not trades_status.get_group('Open').empty:
                        for i, r in trades_status.get_group('Open').iterrows():

                            trades.at[i,'End Time'] = row['Close Time']
                            trades.at[i,'Close Price'] =  row['Close']
                            trades.at[i,'Ratio'] = float(row['Close'])/float(r['Close'])
                            trades.at[i,'PNL'] = 'Profit'
                            trades.at[i,'PNLQ'] = ((float(row['Close'])/float(r['Close']))*100) - 100
                            trades.at[i,'Status'] = 'Close'

                            '''
                            r['End Time'] = row['Close Time']
                            r['Ratio'] = float(row['Close'])/float(r['Close'])
                            r['Close Price'] = row['Close']
                            r['Status'] = 'Close'
                            r['PNLQ'] = ((float(row['Close'])/float(r['Close']))*100) - 100
                            '''
                            if row['Close'] > r['Close']:
                                 trades.at[i,'PNL'] = 'Profit'
                            else:
                                trades.at[i,'PNL'] = 'Loss'


                except:
                    print('All Position is Closed')

                    
    
    
    df = trades.groupby('Status')
    
    return df.get_group('Close')


#backtest for candle pattern max profit strategy

def candlestick_backtest_maxprofit(SYMBOL='',CANDLE_TIMEZONE='',RSI_TIMEZONE='',START_DATE='',END_DATE='',):
    client = Client(config.API_KEY, config.API_SECRET)
    interval = {
        '1m' : Client.KLINE_INTERVAL_1MINUTE ,
        '3m' : Client.KLINE_INTERVAL_3MINUTE ,
        '5m' : Client.KLINE_INTERVAL_5MINUTE ,
        '15m': Client.KLINE_INTERVAL_15MINUTE ,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
    }
    SEARCH_RATE=840000
    if RSI_TIMEZONE == '15m' and CANDLE_TIMEZONE =='1m':
        SEARCH_RATE = 840000
    if RSI_TIMEZONE == '15m' and CANDLE_TIMEZONE =='3m':
        SEARCH_RATE = 840000
    if RSI_TIMEZONE == '5m' and CANDLE_TIMEZONE =='1m':
        SEARCH_RATE = 240000
    if RSI_TIMEZONE == '5m' and CANDLE_TIMEZONE =='3m':
        SEARCH_RATE = 240000
    if END_DATE == '':
        candle_data = client.get_historical_klines(SYMBOL, interval[CANDLE_TIMEZONE],START_DATE)
        rsi_data = client.get_historical_klines(SYMBOL, interval[RSI_TIMEZONE],START_DATE)
    else:
        candle_data = client.get_historical_klines(SYMBOL, interval[CANDLE_TIMEZONE],START_DATE,END_DATE)
        rsi_data = client.get_historical_klines(SYMBOL, interval[RSI_TIMEZONE],START_DATE,END_DATE)
    
    
        
    
    df_candle = pd.DataFrame(candle_data, columns=config.FIELD_HISTORICAL)
    df_rsi = pd.DataFrame(rsi_data, columns=config.FIELD_HISTORICAL)
    set_date(df_candle)
    set_date(df_rsi)
    df_candle = df_candle.copy().iloc[:,:7]
    df_rsi = df_rsi.copy().iloc[:,:7]
    
    psar_candle = SAR(df_candle['High'],df_candle['Low'])
    rsi = RSI(df_rsi['Close'])
    
    
    df_candle['PSAR'] = psar_candle
    df_candle.dropna(inplace=True)
    
    df_rsi['RSI'] = rsi
    df_rsi.dropna(inplace=True)
    
    permisson = False
    res = []
    trades = pd.DataFrame()
    df_candle['PSAR'] = df_candle['PSAR'].astype(str)
    for index, row in df_rsi.iterrows():
        
        if not trades.empty:
            trades_status = trades.groupby(['Status'])
        #trades_status.get_group('Close')
        if row['RSI'] > 50 : 
            permisson  = True
            time = row['Close Time']+1
            search_df = df_candle.loc[(df_candle['Open Time' ] >= time ) & (df_candle['Open Time'] <= time+SEARCH_RATE)]
            positions = search_df[(search_df['Open'] == search_df['High']) & (search_df['Close'] > search_df['Low'] ) & (search_df['PSAR'] > search_df['Close'] )]
            positions.insert(8,'Status', 'Open')
            positions.insert(9,'Margin', 100)
            positions.insert(10,'End Time', '')
            positions['Close Price'] = np.nan
            positions['Ratio'] = np.nan
            positions.insert(13,'PNL', '')
            positions['PNLQ'] = np.nan
            positions['TP']   = positions['PSAR'].copy()
            trades = trades.append(positions)


            if not trades.empty:
                trades_status = trades.groupby(['Status'])
                try:
                    if not trades_status.get_group('Open').empty:
                        open_positions = trades_status.get_group('Open')
                        for ind, ro in trades_status.get_group('Open').iterrows():
                            match_df = search_df.loc[(search_df['Open Time'] > ro['Open Time'])]
                            profit_value =  open_positions['TP'].max()
                            open_positions['TP'] = profit_value
                            for i,r in match_df.iterrows():
                                if profit_value <= r['High']:
                                    trades.at[ind,'End Time'] = r['Open Time']
                                    trades.at[ind,'Close Price'] = profit_value
                                    trades.at[ind,'Ratio'] = float(profit_value)/float(ro['Close'])
                                    trades.at[ind,'PNL'] = 'Profit'
                                    trades.at[ind,'PNLQ'] = ((float(profit_value)/float(ro['Close']))*100) - 100
                                    trades.at[ind,'Status'] = 'Close'
                                    break
                            '''
                            ro['End Time'] = r['Open Time']
                            ro['Close Price'] = ro['Psar']
                            ro['Ratio'] = float(ro['Psar'])/float(ro['Close'])
                            ro['PNL'] = 'Profit'
                            ro['PNLQ'] = ((float(ro['Psar'])/float(ro['Close']))*100) - 100
                            ro['Status'] = 'Close'
                            '''
                except:
                    print('All Position is closed')



        else:
            permission = False
            if not trades.empty:
                trades_status = trades.groupby(['Status'])
                try:
                    if not trades_status.get_group('Open').empty:
                        for i, r in trades_status.get_group('Open').iterrows():

                            trades.at[i,'End Time'] = row['Close Time']
                            trades.at[i,'Close Price'] =  row['Close']
                            trades.at[i,'Ratio'] = float(row['Close'])/float(r['Close'])
                            trades.at[i,'PNL'] = 'Profit'
                            trades.at[i,'PNLQ'] = ((float(row['Close'])/float(r['Close']))*100) - 100
                            trades.at[i,'Status'] = 'Close'

                            '''
                            r['End Time'] = row['Close Time']
                            r['Ratio'] = float(row['Close'])/float(r['Close'])
                            r['Close Price'] = row['Close']
                            r['Status'] = 'Close'
                            r['PNLQ'] = ((float(row['Close'])/float(r['Close']))*100) - 100
                            '''
                            if row['Close'] > r['Close']:
                                 trades.at[i,'PNL'] = 'Profit'
                            else:
                                trades.at[i,'PNL'] = 'Loss'


                except:
                    print('All Position is Closed')

                    
    
    
    df = trades.groupby('Status')
    
    return df.get_group('Close')


# backtest for candlestick patterns futures klines
def candlestick_backtest_futures(SYMBOL='',CANDLE_TIMEZONE='',RSI_TIMEZONE='',START_DATE='',END_DATE='',):
    client = Client(config.API_KEY, config.API_SECRET)
    interval = {
        '1m' : Client.KLINE_INTERVAL_1MINUTE ,
        '3m' : Client.KLINE_INTERVAL_3MINUTE ,
        '5m' : Client.KLINE_INTERVAL_5MINUTE ,
        '15m': Client.KLINE_INTERVAL_15MINUTE ,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
    }
    SEARCH_RATE=840000
    if RSI_TIMEZONE == '15m' and CANDLE_TIMEZONE =='1m':
        SEARCH_RATE = 840000
    if RSI_TIMEZONE == '15m' and CANDLE_TIMEZONE =='3m':
        SEARCH_RATE = 840000
    if RSI_TIMEZONE == '5m' and CANDLE_TIMEZONE =='1m':
        SEARCH_RATE = 240000
    if RSI_TIMEZONE == '5m' and CANDLE_TIMEZONE =='3m':
        SEARCH_RATE = 240000
    if END_DATE == '':
        candle_data = client.futures_historical_klines(SYMBOL, interval[CANDLE_TIMEZONE],START_DATE)
        rsi_data = client.futures_historical_klines(SYMBOL, interval[RSI_TIMEZONE],START_DATE)
    else:
        candle_data = client.futures_historical_klines(SYMBOL, interval[CANDLE_TIMEZONE],START_DATE,END_DATE)
        rsi_data = client.futures_historical_klines(YMBOL, interval[RSI_TIMEZONE],START_DATE,END_DATE)
    
    
        
    
    df_candle = pd.DataFrame(candle_data, columns=config.FIELD_HISTORICAL)
    df_rsi = pd.DataFrame(rsi_data, columns=config.FIELD_HISTORICAL)
    set_date(df_candle)
    set_date(df_rsi)
    df_candle = df_candle.copy().iloc[:,:7]
    df_rsi = df_rsi.copy().iloc[:,:7]
    
    psar_candle = SAR(df_candle['High'],df_candle['Low'])
    rsi = RSI(df_rsi['Close'])
    
    
    df_candle['PSAR'] = psar_candle
    df_candle.dropna(inplace=True)
    
    df_rsi['RSI'] = rsi
    df_rsi.dropna(inplace=True)
    
    permisson = False
    res = []
    trades = pd.DataFrame()
    df_candle['PSAR'] = df_candle['PSAR'].astype(str)
    for index, row in df_rsi.iterrows():
        
        if not trades.empty:
            trades_status = trades.groupby(['Status'])
        #trades_status.get_group('Close')
        if row['RSI'] > 50 : 
            permisson  = True
            time = row['Close Time']+1
            search_df = df_candle.loc[(df_candle['Open Time' ] >= time ) & (df_candle['Open Time'] <= time+SEARCH_RATE)]
            positions = search_df[(search_df['Open'] == search_df['High']) & (search_df['Close'] > search_df['Low'] ) & (search_df['PSAR'] > search_df['Close'] )]
            positions.insert(8,'Status', 'Open')
            positions.insert(9,'Margin', 100)
            positions.insert(10,'End Time', '')
            positions['Close Price'] = np.nan
            positions['Ratio'] = np.nan
            positions.insert(13,'PNL', '')
            positions['PNLQ'] = np.nan
            positions
            trades = trades.append(positions)


            if not trades.empty:
                trades_status = trades.groupby(['Status'])
                try:
                    if not trades_status.get_group('Open').empty:
                        for ind, ro in trades_status.get_group('Open').iterrows():
                            match_df = search_df.loc[(search_df['Open Time'] > ro['Open Time'])]
                            for i,r in match_df.iterrows():
                                if ro['PSAR'] <= r['High']:
                                    trades.at[ind,'End Time'] = r['Open Time']
                                    trades.at[ind,'Close Price'] = ro['PSAR']
                                    trades.at[ind,'Ratio'] = float(ro['PSAR'])/float(ro['Close'])
                                    trades.at[ind,'PNL'] = 'Profit'
                                    trades.at[ind,'PNLQ'] = ((float(ro['PSAR'])/float(ro['Close']))*100) - 100
                                    trades.at[ind,'Status'] = 'Close'
                                    break
                            '''
                            ro['End Time'] = r['Open Time']
                            ro['Close Price'] = ro['Psar']
                            ro['Ratio'] = float(ro['Psar'])/float(ro['Close'])
                            ro['PNL'] = 'Profit'
                            ro['PNLQ'] = ((float(ro['Psar'])/float(ro['Close']))*100) - 100
                            ro['Status'] = 'Close'
                            '''
                except:
                    print('All Position is closed')



        else:
            permission = False
            if not trades.empty:
                trades_status = trades.groupby(['Status'])
                try:
                    if not trades_status.get_group('Open').empty:
                        for i, r in trades_status.get_group('Open').iterrows():

                            trades.at[i,'End Time'] = row['Close Time']
                            trades.at[i,'Close Price'] =  row['Close']
                            trades.at[i,'Ratio'] = float(row['Close'])/float(r['Close'])
                            trades.at[i,'PNL'] = 'Profit'
                            trades.at[i,'PNLQ'] = ((float(row['Close'])/float(r['Close']))*100) - 100
                            trades.at[i,'Status'] = 'Close'

                            '''
                            r['End Time'] = row['Close Time']
                            r['Ratio'] = float(row['Close'])/float(r['Close'])
                            r['Close Price'] = row['Close']
                            r['Status'] = 'Close'
                            r['PNLQ'] = ((float(row['Close'])/float(r['Close']))*100) - 100
                            '''
                            if row['Close'] > r['Close']:
                                 trades.at[i,'PNL'] = 'Profit'
                            else:
                                trades.at[i,'PNL'] = 'Loss'


                except:
                    print('All Position is Closed')

                    
    
    
    df = trades.groupby('Status')
    
    return df.get_group('Close')
