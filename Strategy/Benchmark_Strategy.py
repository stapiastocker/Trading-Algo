#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 26 20:09:44 2018

@author: bas
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os


def benchmark_strategy(Equity2 = 1, ma_df = pd.DataFrame(data={'Close':np.random.rand(100), '20ma':np.random.rand(100), '50ma':np.random.rand(100)})): #pd.DataFrame(data={'Close':0, '20ma':0, '50ma':0}
    Balance = [Equity2]
    Benchmark_Balance = [Equity2]
    CoinsOwned = 0
    CoinsOwed = 0
    Short_equity = 0
    #Benchmark Strategy
    for i in ma_df.index:
        #Crossover
        if (ma_df.iloc[i,1] > ma_df.iloc[i,2]) and (ma_df.iloc[i-1,1] < ma_df.iloc[i-1,2]):
            #Close Short
            if CoinsOwed > 0:
                Balance.append(Balance[-1]+(Short_equity - ma_df['Close'][i]*CoinsOwed))
                CoinsOwed = 0
            #Open Long
            CoinsOwned = (Balance[-1]/ma_df['Close'][i])
#            plt.annotate('', xy=(df['Date'][i-1],df['Close'][i]),
#                             xytext=(df['Date'][i+1], df['Close'][i]),
#                             arrowprops=dict(arrowstyle="-",
#                             color='y',lw=2))
        #Crossunder
        elif (ma_df.iloc[i,1] < ma_df.iloc[i,2]) and (ma_df.iloc[i-1,1] > ma_df.iloc[i-1,2]):
            #Close Long
            if CoinsOwned > 0:
                Balance.append(ma_df['Close'][i]*CoinsOwned)
                CoinsOwned = 0
            #Open Short
            Short_equity = Balance[-1]
            CoinsOwed = (Balance[-1]/ma_df['Close'][i]) #gets you the coins you owe 
#           plt.annotate('', xy=(df['Date'][i-1],df['Close'][i]),
#                             xytext=(df['Date'][i+1], df['Close'][i]),
#                             arrowprops=dict(arrowstyle="-",
#                             color='m',lw=2))
        
        else:
            Balance.append(Balance[-1])
        
        #If neither a short or long is opened then append the curent balance value.
        #With two different lists for balance you have short values being compared to the right balance value. 
        if CoinsOwned > 0: #There is always a short or long happening expect for the beginning
            Benchmark_Balance.append(ma_df['Close'][i]*CoinsOwned) #Adds up total balance every day, if there haven't been any trades. 
        elif CoinsOwed > 0:
            Benchmark_Balance.append(Balance[-1] + (Short_equity - ma_df['Close'][i]*CoinsOwed))
        else:
            Benchmark_Balance.append(Benchmark_Balance[-1])
    
#    HODL = df['Close'] * (Equity2/df['Close'][0])
    #plt.plot(Benchmark_Balance)
#    plt.plot(HODL)
    #plt.show
    return Benchmark_Balance 
    #Try sending it over to main module and see if it works. Seems like it works

benchmark_strategy()
