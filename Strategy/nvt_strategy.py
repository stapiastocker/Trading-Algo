#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 22 17:44:29 2018

@author: bas
"""
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path
#Own Modules
import Benchmark_Strategy as BStrat
import SortinoRatio as sr
import nvt_signal as nvt
style.use("ggplot")

prices = 'crypto_data_download/coindesk-bpi-USD-close_data-2010-07-18_2018-08-23.csv'  # 'bitcoin-historical-data/coindesk-bpi-USD-2017-09-03_2018-08-15.csv'
prices_timestamp = 'crypto_data_download/coindesk-bpi-USD-close_data-2010-07-18_2018-08-23_timestamp.csv'

def compile_data(dir_csv = prices, new_csv =prices_timestamp):
    '''
    Docstring
    '''    
    dir_csv = Path(dir_csv)
    new_csv = Path(new_csv)
    #coindesk data needs to be trimmed. Date is of type string.
    if not new_csv.exists():
        df = pd.read_csv(dir_csv)
        
        with open(new_csv, 'w') as f:
            df['Date'] = df['Date'].apply(lambda x: x.rstrip('00:00'))
#            try:
#                df['Date'] = pd.to_datetime(df['Date'], format = '%d/%m/%y')
#            except ValueError:
#                pass
            df.to_csv(f)
    
    df = pd.read_csv(new_csv)
    df.drop(df.columns[0], axis=1, inplace = True)
    
    return df

df = compile_data() 

df_NVT = nvt.nvt_signal(df = df) 

def moving_average(MA_choices=(20, 50)):
    ma_df = pd.DataFrame(df_NVT['Close']) #This just creates an empty dataframe. index = df['Date']
    for i in MA_choices:
        ma_df['{}ma'.format(i)] = df_NVT['Close'].rolling(window = i).mean()
    
    return ma_df

ma_df = moving_average()

#Shorting Logic: 
#Short can only start if the CoinsOwed is equal to 0.
#The Short Equity is based on the previous balance, so if we hold 10,000 dollars, 10,000 dollars will be borrowed. 
#To calculate the number of coins we borrow we take the previous balance and divide it by the current close, this is then multiplied by the commission.

#Commission used is the market order fee on kraken. The change from 0.0005 (Binance's fee) is noticeable but the effect is not substantial
def strategy(Equity = 1000, commission = 0.0026, rollover_fee = 0.0001): 
    MA_df = moving_average()
    
    Benchmark_Balance = BStrat.benchmark_strategy(Equity2 = Equity, ma_df = MA_df) #Go to Benchmark_Strategy
    
    #NVT strategy
    Balance = [Equity]
    Strategy_Balance =[Equity]
    Coins_Owned = 0
    Coins_Owed = 0
    Shorts_Allowed =False
    Short_equity = 0
    Hodl_Start= True
    Hodl_Coins = 0
    Hodl_Index = 0
    for i in df_NVT.index:
        #End Short And Go Long 
        if df_NVT.iloc[i,1] <= 45 and (df_NVT.iloc[i-1,1] > 45):
            if Hodl_Start == True:
                Hodl_Coins = Equity/df_NVT['Close'][i]
                Hodl_Index = i
                Hodl_Start = False
            #Close Short
#            if CoinsOwed > 0:
#                Balance.append(Balance[-1]+ (Short_equity - df_NVT['Close'][i]*CoinsOwed*(1+commission)))
#                CoinsOwed = 0
            #Open Long
            if Coins_Owned == 0:
                Coins_Owned = (Balance[-1]/df_NVT['Close'][i])*(1-commission)
                plt.axvline(x = i+1, color='#32CD32') #Plus 1 had to be added as lines were 1 day to early compared to the buy in price. This is because index values are being used for iteration. 
            Shorts_Allowed = True
        #End Long And Go Short
        elif df_NVT.iloc[i,1] >= 170  and df_NVT.iloc[i-1,1] < 170 and Shorts_Allowed == True:
            #Close Long
            if Coins_Owned > 0:
                Balance.append(df_NVT['Close'][i]*Coins_Owned*(1-commission))
                Coins_Owned = 0
                plt.axvline(x = i, color='r')
            #Open Short
#            if CoinsOwed == 0:
#                if Balance[-1] < 500000: #500,000 is margin limit in kraken
#                    Short_equity = Balance[-1]
#                else:
#                    Short_equity = 500000
#                CoinsOwed = (Short_equity/df_NVT['Close'][i])*(1+commission)
#                plt.axvline(x = i+1, color='r')
        else:
            Balance.append(Balance[-1])
        
        #Daily Balance of Strategy. Shows how the portfolio changes every day. 
        if Coins_Owned > 0:
            Strategy_Balance.append(df_NVT['Close'][i]*Coins_Owned) 
            
#        elif CoinsOwed > 0:
#            Strategy_Balance.append(Balance[-1] + (Short_equity*(1-rollover_fee)**6 - df_NVT['Close'][i]*CoinsOwed))
            #print("Date: " +str(df_NVT['Time'][i]) + ", Balance: "+str(Balance[-1]) + ", Strategy Balance: " + str(Strategy_Balance[-1]))
            #print("Date: " +str(df_NVT['Time'][i]) +" "+ str(short_test))
        
        else:
            Strategy_Balance.append(Strategy_Balance[-1])
        
        
    #HODL
    HODL = pd.Series(0, index=[i for i in range(Hodl_Index)]).append(df_NVT['Close'][Hodl_Index:]*Hodl_Coins)

    #Sortino Ratios
    HODL_SR = round(sr.sortino_ratio(Y = HODL[175:]),3)
    Benchmark_Strategy = pd.DataFrame(Benchmark_Balance,columns = ['Balance'])
    Benchmark_Strategy_SR = round(sr.sortino_ratio(Y = Benchmark_Strategy['Balance']),3)
    Strategy = pd.DataFrame(Strategy_Balance,columns = ['Balance'])
    Strategy_SR = round(sr.sortino_ratio(Y = Strategy['Balance']),3)
    
    
    #Plots
    plt.plot(Benchmark_Balance, label ='Benchmark Balance', color ='b')
    plt.plot(HODL, label = 'Hodl'+", Buy Date: " +df_NVT['Time'][Hodl_Index], color = 'r')
    plt.plot(Strategy_Balance, label  = 'NVT Strategy', color ='g')
    #plt.plot(df_NVT['Close'])
    #plt.plot(Balance)
    plt.plot([None], [None], ' ', label="Strategy SR: "+str(Benchmark_Strategy_SR))
    plt.plot([None], [None], ' ', label="Hodl SR: "+str(HODL_SR))
    plt.plot([None], [None], ' ', label="Strategy SR: "+str(Strategy_SR))
    plt.title("BTC vs USD With Starting Equity of $"+str(Equity))
    plt.xticks(rotation=90)
    plt.legend()
    plt.show()

strategy(Equity = 100)
