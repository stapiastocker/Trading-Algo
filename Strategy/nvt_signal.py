#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 26 23:10:18 2018

@author: bas
"""

import bs4 as bs
import requests
import datetime as dt
import pandas as pd
import numpy as np

def nvt_signal(Refresh_Data = False, df = pd.DataFrame(data={'Date':[0], 'Close':[0]})):
    if Refresh_Data == True:
        headers = {'USER-AGENT': 'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405'}
        sauce = requests.get('https://plot.ly/~bastapia/5.embed', headers = headers) 
        soup = bs.BeautifulSoup(sauce.content, 'lxml')
        
        table = soup.table
        table_rows = table.find_all('tr')
        Time_NVT = {'Time':[], 'NVT_Ratio':[]}
        for tr in table_rows[1:]: #iterates through each row
            td = tr.find_all('td') #in the tr row it searches for all the separate data tags. 
            row = [i.text for i in td]
            if '' not in row:  #good the if statement works and is alot more succinct 
                row[0] = row[0].strip('00:00').strip()
                row[0] = dt.datetime.strptime(row[0], '%Y-%m-%d').strftime('%d/%m/%y') #gucci
                Time_NVT['Time'].append(row[0])
                Time_NVT['NVT_Ratio'].append(float(row[2]))
        
        #Code is neater now. 
        df_NVT = pd.DataFrame(data = Time_NVT)
        with open('NVT.csv', 'w') as f:
            df_NVT.to_csv(f)
    else:
        df_NVT = pd.read_csv('NVT.csv')
        df_NVT.drop(df_NVT.columns[0], axis=1, inplace = True)
    
    #getting price data for Time values
    df_2 = df.loc[df['Date'].isin(df_NVT['Time'])] 
    
    #Add Closing prices to df_NVT
    df_NVT['Close'] = df_2['Close'].values
    
    #Identifying Oversold conditions
    df_Buy = df_NVT.loc[df_NVT['NVT_Ratio'] < 45]
    
    return df_NVT
    
    #Plot
#    ax1 = plt.subplot2grid((2,1), (0,0))
#    plt.xticks(rotation=45)
#    ax2 = plt.subplot2grid((2,1), (1,0), sharex = ax1)
#    plt.axhline(45, color='b', ls='dashed')
#    plt.axhline(150, color='b', ls='dashed')
#    plt.xticks(rotation=90)
#    
#    ax1.semilogy(df_NVT['Time'][400:],df_2['Close'][400:], color = 'r')
#    ax1.set_yscale('log')
#    plt.setp(ax1.get_xticklabels(), visible = False)
#    
#    ax2.plot(df_NVT['Time'][400:],df_NVT['NVT_Ratio'][400:], color = 'y')
#    plt.setp(ax2.get_xticklabels(), visible = False)
#    for i in df_Buy['Time']:
#        ax2.axvline(x = i)
    
    #plt.show()
