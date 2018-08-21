#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 23:43:39 2018

@author: bas
"""

import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from mpl_finance import candlestick_ohlc
import pandas as pd
import os

style.use("ggplot")


def compile_data():
    '''
    Function compiles data from csvs.
    Bear in mind that datasets have differing representations of time abd the function doesn't adjust to these differences.
    For different csv files the code needs to be changed to remove odd characters so that it can be converted to a datetime object. 
    
    '''
    dir_csv =  'crypto_data_download/Gdax_BTCUSD_d.csv'#'bitcoin-historical-data/coindesk-bpi-USD-2017-09-03_2018-08-15.csv'
    new_csv = 'crypto_data_download/Gdax_BTCUSD_d_mdates.csv'
    
    if not os.path.exists(new_csv):
        df = pd.read_csv(dir_csv)
        
        with open(new_csv, 'w') as f:
            #df['Date'] = df['Date'].apply(lambda x: x.strip('-PM'))
            #df['Date'] = df['Date'].apply(lambda x: x.strip('-AM'))
            df['Date'] = pd.to_datetime(df['Date'], format = '%d/%m/%y')
            df['Date'] = df['Date'].apply(mdates.date2num)
            df.set_index('Date', inplace=True)
            df.sort_index(ascending=True, inplace = True)
            df.to_csv(f)
    
    df = pd.read_csv(new_csv) 
    
    return df

df = compile_data()
X = df['Close']

def sortino_ratio(Y = []):
    '''
    Sortino Ratio is a measure of how much extra return an asset generates per unit of downside volatilty.
    The extra return is normally determined by the differnece between the avg return of an asset and the avg return of a risk-free asset (e.g. treasury bonds)
    Sortino Ratio = (AvgReturn - RiskFreeReturn)/(Downside Deviation)
    
    Currently risk adjusted return is set to 0%
    '''
    #Current Sortino Ratio calculation is based on Red Rock CME group. 
    
    #Daily Return
    Return = (Y.pct_change()).tolist() #pct_change in decimal form
    Avg_Return = sum(Return[1:])/len(Return)
    
    #Risk-Free return (for assigned period)
    Daily = ((2.5/100 + 1)**(1/365) - 1)*100
    
    #Downside Standard Deviation
    N_Returns_Sqrt = [(i**2) if i < 0.0 else 0.0 for i in Return]
    Down_Dev = (sum(N_Returns_Sqrt)/(len(N_Returns_Sqrt)))**(1/2)
    
    #Sortino Ratio
    Sortino_Ratio = (Avg_Return)/Down_Dev
    
    return Sortino_Ratio


def moving_average(MA_choices = [20,50]):
    '''
    This function allows you to input a list of desired MA.
    They need to be in order for other functions to operate. 
    '''
    df = compile_data()
    ma_df = pd.DataFrame(df['Close'])
    for i in MA_choices:
        ma_df['{}ma'.format(i)] = df['Close'].rolling(window = i).mean()
    
    return ma_df
    
#moving_average()


def rsi_data(period = 14):
    '''
    First make a dataframe specifically for RSI. 
    Append the close price for all the days. 
    Next calculate the change in price between dates, positive and negative
    After 14 closes, calculate the average gain and average loss of the last 14 (You should be able to differentiate between positive and negative change). 
    Subsequently, find the RS and RSI of the 14th period.
    For the following close prices, continue to calculate the avg. gain/loss and RS. For the RSI though you need to take into account the previous value. 
    '''
    df = compile_data()
    rsi_df = df[['Close']]
    
    change = [0]
    up = [0]
    down = [0]
    L = len(rsi_df['Close'])
    #Loop determines the change in closing price between successive days. 
    for i in range(1,L):
        x = rsi_df['Close'][i] - rsi_df['Close'][i-1]
        change.append(x)  
        if (x) > 0:
            up.append(x)
            down.append(0)
        else:
            up.append(0)
            down.append(abs(x))
    
    NaN_filler = [None for i in range(period)]
    avg_gain = NaN_filler.copy() 
    avg_loss = NaN_filler.copy()
    
    #This splits up positive changes in price from negative ones into two separate lists. 
    #After 'period' number of iterations it sums the gains and losses separately over the period and divides by the period. 
    for i in range(period,L):
        gain = []
        loss = []
        for j in range(i-period, i):
            if change[j]>0:
                gain.append(change[j])
            elif change[j]<0:
                loss.append(change[j])
        avg_gain.append(sum(gain)/period)
        avg_loss.append(abs(sum(loss)/period))
        
    #RS and RSI calculation
    RS = NaN_filler.copy() + [avg_gain[period]/avg_loss[period]] 
    RS += [((avg_gain[z]*(period-1) + x)/period)/((avg_loss[z]*(period-1) + y)/period) for x, y, z in zip(up[period+1:], down[period+1:], range(period,L))]
    # Smooth RS logic. First calculate the RS. The next period needs the smoothed RS. This is calculated by multiplying the average gain of the previous period by 13 adding on the current gain
    #It's the avg_gain and loss in zip thats the issue. You need to be adding the current gain to the avg_gain*13. 
    RSI = NaN_filler.copy() + [100 - (100/(1+i)) for i in RS[period:]]
    
    rsi_df['Change'] = change
    rsi_df['Up'] = up #up and down are successfully splitting the rises and falls. 
    rsi_df['Down'] = down
    rsi_df['AvgGain'] = avg_gain
    rsi_df['AvgLoss'] = avg_loss
    rsi_df['RS'] = RS
    rsi_df['RSI'] = RSI
    
    return rsi_df #remember always to put the right pandas name. 

#rsi_data()

def TD_Sequential():
    '''
    "Applying the TD Sequential serves the purpose of identifying a price point where an uptrend or a downtrend exhausts itself and reverses."

    TD Sequential has two parts – TD Setup and TD Countdown. 
    The first phase of TD Sequential starts with a TD Setup and is completed with a 9 count. 
    When the 9 count is completed, it is at that point, a price pause, price pullback, or reversal is likely. 
    It is also at that point where TD Sequential starts the second phase with TD Countdown and is completed with a 13 count. 
    When the 13 count is recorded, it is at that point, a price pause, price pullback, or a reversal is likely.
    '''
    df = compile_data()
     
    TDSL=0
    TDSS=0
    BuySetup=0
    SellSetup=0
    BuyCountdown=0
    SellCountdown=0 
    
    
    W = df['High']
    X = df['Close']
    Y = df['Low']
    Z = df['Date']
    bearishflip = 0
    bullishflip = 0
    for i in range(5,len(df.index)):
        if X[i-1]>X[i-5] and X[i]<X[i-4]:
            bearishflip=1
            bullishflip=0
        elif X[i-1]<X[i-5] and X[i]>X[i-4]:
            bullishflip=1
            bearishflip=0
        if X[i]<X[i-4] and (bearishflip == 1):
            TDSL += 1
            TDSS = 0
        elif X[i]>X[i-4] and (bullishflip ==1):
            TDSS += 1
            TDSL = 0
        #Red
        if TDSL>0 and TDSL<10:
            plt.text(Z[i], W[i]*1.02, "{}".format(TDSL), color = 'r', size ='x-small')
        if TDSL==9:
            L=(Y[i]<Y[i-3] and Y[i]<Y[i-2]) or (Y[i-1]<Y[i-2] and Y[i-1]<Y[i-3])
            bearishflip=0
            TDSL=0
            BuySetup=1
            if L == True:
                plt.annotate('', xy=(Z[i],Y[i]*0.98),
                             xytext=(Z[i], Y[i]*0.96),
                             arrowprops=dict(arrowstyle="-|>",
                             color='g',lw=1.5))
        #Green
        if TDSS>0 and TDSS<10:
            plt.text(Z[i], Y[i]*0.98, "{}".format(TDSS), color = 'g', size ='x-small')
        if TDSS==9:
            S=(W[i]>W[i-2] and W[i]>W[i-3]) or (W[i-1]>W[i-3] and W[i-1]>W[i-2])
            bullishflip=0
            TDSS=0
            SellSetup=1
            if S == True:
                plt.annotate('', xy=(Z[i],W[i]*1.02),
                             xytext=(Z[i], W[i]*1.04),
                             arrowprops=dict(arrowstyle="-|>",
                             color='r',lw=1.5))
        #Green
        if BuySetup == True:
            if X[i]<=Y[i-2]:
                BuyCountdown+=1
                plt.text(i, Y[i]*0.97, "{}".format(BuyCountdown), color = 'b')
            if BuyCountdown==8:
                Bar8=i
            elif BuyCountdown==13:
                if Y[i]<=X[i-Bar8]:
                    plt.annotate('', xy=(Z[i],Y[i]*0.98),
                             xytext=(Z[i], Y[i]*0.96),
                             arrowprops=dict(arrowstyle="-|>",
                             color='g',lw=1.5))
                BuySetup=0
                BuyCountdown=0
        #Red
        elif SellSetup == True:
            if X[i]>=W[i-2]:
                SellCountdown+=1
                plt.text(i, W[i]*1.02, "{}".format(SellCountdown), color = 'b')
            if SellCountdown==8:
                Bar8=i
            elif SellCountdown==13:
                if W[i]>=X[i-Bar8]:
                    plt.annotate('', xy=(Z[i],W[i]*1.02),
                             xytext=(Z[i], W[i]*1.04),
                             arrowprops=dict(arrowstyle="-|>",
                             color='r',lw=1.5))
                SellSetup=0
                SellCountdown=0
                    
#TD_Sequential()

def strategy(Equity = 1000, commission = 0.0005):
    '''
    Currently Strategy just has the benchmark strat which is based on the MA crossovers.
    '''
    df = compile_data()
    ma_df = moving_average()
    
    Balance = [Equity]
    Bench_Balance = [Equity]
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
            plt.annotate('', xy=(df['Date'][i-1],df['Close'][i]),
                             xytext=(df['Date'][i+1], df['Close'][i]),
                             arrowprops=dict(arrowstyle="-",
                             color='y',lw=2))
        #Crossunder
        elif (ma_df.iloc[i,1] < ma_df.iloc[i,2]) and (ma_df.iloc[i-1,1] > ma_df.iloc[i-1,2]):
            #Close Long
            if CoinsOwned > 0:
                Balance.append(ma_df['Close'][i]*CoinsOwned)
                CoinsOwned = 0
            #Open Short
            Short_equity = Balance[-1]
            CoinsOwed = (Balance[-1]/ma_df['Close'][i]) #gets you the coins you owe 
            plt.annotate('', xy=(df['Date'][i-1],df['Close'][i]),
                             xytext=(df['Date'][i+1], df['Close'][i]),
                             arrowprops=dict(arrowstyle="-",
                             color='m',lw=2))
        else:
            Balance.append(Balance[-1])
        
        
        #Portfolio Value Calculation for every day. 
        if CoinsOwned > 0: 
            Bench_Balance.append(ma_df['Close'][i]*CoinsOwned) #Adds up total balance every day, if there haven't been any trades. 
        elif CoinsOwed > 0:
            Bench_Balance.append(Balance[-1] + Short_equity - ma_df['Close'][i]*CoinsOwed)
        else:
            Bench_Balance.append(Bench_Balance[-1])
            
    #HODL
    HODL = ma_df['Close']*(Equity/ma_df['Close'][0])
    
    #Sortino Ratios
    HODL_SR = round(sortino_ratio(Y = HODL),3)
    strategy = pd.DataFrame(Bench_Balance,columns = ['Balance'])
    Strategy_SR = round(sortino_ratio(Y = strategy['Balance']),3)
    
    #Plots
    plt.plot(Bench_Balance, label ='Benchmark Balance')
    plt.plot(ma_df.index, HODL, label = 'Hodl')
    plt.plot([None], [None], ' ', label="Hodl SR: "+str(HODL_SR))
    plt.plot([None], [None], ' ', label="Strategy SR: "+str(Strategy_SR))
    plt.legend()
    plt.show()
    
strategy(100000)
            
        
                
def visualise_data():
    #Data
    df = compile_data()
    rsi_df = rsi_data()
    ma_df = moving_average([20,50,100])
    
    
    #Subplot definitions and visual code for specific plots  
    ax1 = plt.subplot2grid((6,1), (5,0), rowspan = 1, colspan = 1)
    plt.xticks(rotation=45)
    plt.axhline(30, color='b', ls='dashed')
    plt.axhline(70,color='b', ls='dashed')
    ax2 = plt.subplot2grid((6,1), (0,0), rowspan = 5, colspan = 1, sharex = ax1)
    
    #RSI Plot
    ax1.plot(df['Date'], rsi_df['RSI'])
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    
    #Candlestick plot
    ohlc = df[['Date','Open', 'High', 'Low', 'Close']]
    candlestick_ohlc(ax2, ohlc.values,  width = 0.6, colorup='green')
    
    #TD Sequential
    #TD_Sequential()
    
    #MA plotting
    for i in ma_df.columns[1:]:
        ax2.plot(df['Date'], ma_df[i], linewidth=1.0)
    
    #Visual tweaks to plots
    plt.setp(ax2.get_xticklabels(), visible = False)
    plt.ylabel("Price (USD)") 
    plt.title("Daily BTC Prices")
    plt.subplots_adjust(top=0.935,bottom=0.15,left=0.11,right=0.9,hspace=0.2,wspace=0.2)
    Crossover = mpatches.Patch(color='yellow', label='Crossover ')
    Crossunder = mpatches.Patch(color='purple', label='Crossunder ')
    plt.legend(handles=[Crossover, Crossunder])

    plt.show()
    
#visualise_data()



    