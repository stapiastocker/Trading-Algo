#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 26 23:02:25 2018

@author: bas
"""

def sortino_ratio(Y = []):
    '''
    Sortino Ratio is a measure of how much extra return an asset generates per unit of downside volatilty.
    The extra return is normally determined by the differnece between the avg return of an asset and the avg return of a risk-free asset (e.g. treasury bonds)
    '''
    
    #Current Sortino Ratio calculation is based on Red Rock CME group. 
    
    #Daily Return
    Return = (Y.pct_change()).tolist() #pct_change in decimal form
    Avg_Return = sum(Return[1:])/len(Return)
    
    #Risk-Free return (for assigned period)
    #Daily = ((2.5/100 + 1)**(1/365) - 1)*100
    
    
    #Downside Standard Deviation
    N_Returns_Sqrt = [(i**2) if i < 0.0 else 0.0 for i in Return]
    Down_Dev = (sum(N_Returns_Sqrt)/(len(N_Returns_Sqrt)))**(1/2)
    
    
    #Sortino Ratio
    Sortino_Ratio = (Avg_Return)/Down_Dev
    
    return Sortino_Ratio

