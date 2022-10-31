from gettext import find
from postion import Position
from account import Account
import yfinance as yf
import pandas as pd
from os import path
from datetime import date, timedelta
import os
from progressbar import ProgressBar
import numpy as np
from scipy.stats import linregress
import PySimpleGUI as sg
import random
import pandas_ta as pta
from csv import DictWriter

def download(stock, period):
    data = yf.download(stock, period = period)
    return data

def trenddetector(index, data, order = 1):
    coeffs = np.polyfit(index, list(data), order)
    slope = coeffs[-2]
    return float(slope)

def momentum(data):
    returns = np.log(data)
    x = np.arange(len(returns))
    slope, _, rvalue, _, _ = linregress(x, returns)
    return ((1 + slope) ** 252) * (rvalue ** 2)

# SMA Crossover analysis
def crossOver(rolling20, rolling5, data):
    j = len(rolling20)
    i = len(data)
    ratio = rolling5[j-1] / data[i-1]
    if rolling20[j-4] > rolling5[j-4] and rolling5[j-1] > rolling20[j-1] and ratio > .991 and ratio < 1:
        return True

# Breakthrough analysis
def breakThrough(data, rolling5):
    j = len(data)
    if data[j-1] < rolling5[j-1]:
        return True

def find_rsi(df, periods = 14, ema = True):
    return pta.rsi(df, length=14)

def bollinger_bands(data, stockList):
    picks = []
    for i in range(0, len(stockList)):
        rollingData = data[stockList[i]]
        if rollingData.empty:
            pass
        #print(rollingData.head())
        short = rollingData.rolling(5).mean()
        short = short.tolist()
        lon = rollingData.rolling(20).mean()
        std = rollingData.rolling(20).std()
        upper_bollinger = lon + std * 2
        lower_bollinger = lon - std * 2
        lon = lon.tolist()
        lower_bollinger = lower_bollinger.tolist()
        upper_bollinger = upper_bollinger.tolist()
        ds = rollingData.tolist()
        rsi = find_rsi(rollingData).tolist()[-1]

        dataslope = trenddetector(list(range(0, 3)), ds[-3:])

        # Buy signals
        # 1) Price is above lower band
        # 2) Stock price has been rising for last 3 days
        # 3) Price is lower than 20 MA
        # 4) 5MA just crossed over the 20MA
        if ds[-1] > lower_bollinger[-1] and dataslope > 0 and ds[-1] < lon[-1]:
            picks.append((stockList[i],ds[-1],lower_bollinger[-1], rsi))
        elif short[-1] > lon[-1] and short[-2] < lon[-2]:
            picks.append((stockList[i],ds[-1],lower_bollinger[-1], rsi))

    # Sort from low to high RSI as lower RSI means oversold  
    picks.sort(key = lambda x: x[3])
    return picks

def simple_buy(data, stockList):
    picks = []
    for i in range(0, len(stockList)):
        rollingData = data[stockList[i]]
        if rollingData.empty:
            pass
        #print(rollingData.head())
        short = rollingData.rolling(5).mean()
        short = short.tolist()
        lon = rollingData.rolling(20).mean()
        std = rollingData.rolling(20).std()
        upper_bollinger = lon + std * 2
        lower_bollinger = lon - std * 2
        lon = lon.tolist()
        lower_bollinger = lower_bollinger.tolist()
        upper_bollinger = upper_bollinger.tolist()
        ds = rollingData.tolist()
        rsi = find_rsi(rollingData).tolist()[-1]

        MASlope20 = trenddetector(list(range(0, 3)), lon[-3:])
        dataslope = trenddetector(list(range(0, 3)), ds[-3:])

        if MASlope20 > 0.5 and lon[-1] > short[-1]:
            picks.append((stockList[i],ds[-1], rsi))
    
    return picks

def stocks_to_buy(account, picks):
    if account.free_capital > 10: 
        buying = picks[:int(.05*len(picks))]
        for s in buying:
            new_pos = Position(s[0], s[1], (account.free_capital * .1))
            account.buy_position(new_pos)

def stocks_to_sell(account, data):
    if account.positions:
        date = data["Date"].tolist()[0]
        sell = []
        for pos in account.positions:
            rollingData = data[pos]
            if rollingData.empty:
                pass
            #print(rollingData.head())
            short = rollingData.rolling(5).mean()
            short = short.tolist()
            lon = rollingData.rolling(20).mean()
            std = rollingData.rolling(20).std()
            upper_bollinger = lon + std * 2
            lower_bollinger = lon - std * 2
            lon = lon.tolist()
            lower_bollinger = lower_bollinger.tolist()
            upper_bollinger = upper_bollinger.tolist()
            ds = rollingData.tolist()
            MASlope20 = trenddetector(list(range(0, 3)), lon[-3:])

            # Sell triggers
            # 1) Value of position has dropped to 5% below start
            # 2) 20MA crosses above 5MA
            # 3) 20MA slope drops to lower then .25 (momentum declining)
            if account.positions[pos]['value'] < account.positions[pos]['start_price']:
                if float((account.positions[pos]['start_price'] - account.positions[pos]['value'])/account.positions[pos]['start_price']) > .03:
                    sell.append(pos)
            elif lon[-1] > short[-1]:
                sell.append(pos)
            elif MASlope20 < 0.25:
                sell.append(pos)
        
        field_names = ['Date','Ticker', 'Start_Value', 'Sale_Value', 'Account_Value', 'Total_Invested']
        for ticker in sell:
            row = {'Date':date, 'Ticker': ticker, 'Start_Value': account.positions[ticker]['start_price'], 'Sale_Value': account.positions[ticker]['value'], 'Account_Value': account.get_value(), 'Total_Invested': account.get_total_invested()}
            account.sell_position(ticker)
            with open('sales_test.csv', 'a', newline='') as f_object:
                dictWriter_obj = DictWriter(f_object, fieldnames=field_names)
                dictWriter_obj.writerow(row)
                f_object.close()


def analyze(data, tickers, end, choice):
    counter = 0
    watchList = []
    for i in range(0, end):
        # Download Ticker info
        trend = data[tickers[i]]
        counter = counter+1
        if trend.empty:
            pass
        else:
            trendList = trend.tolist()
            # Only care about close data for now
            if (trendList[-1] < 600):# and ():
                watchList.append(tickers[i])
    return bollinger_bands(data, watchList)

def check_postions(stock_data, account):
    # define selling positions and updating account and positions here
    # conditions
    #   1) Lost 5% on trade
    #   2) Gained 10% on trade
    #   3) Stock goes below 20 MA (crossover specific)
    if account.positions:
        for pos in account.positions:
            cur_price = stock_data.loc[:,pos].tolist()[-1]
            account.update_postion(pos, cur_price)
        stocks_to_sell(account, stock_data)

def test_wrapper(stock_data, tickers, account):
    print(f'Begin Test!!!\n\t{account.name} current value : {account.value}')
    # Run over 60 data sets for each interval
    i = 0
    rows = data.shape[0]
    while i < rows - 60:
        picks = []
        check_postions(data.iloc[i:61+i,:], account)
        picks = analyze(data.iloc[i:61+i,:], tickers, len(tickers), 3)
        stocks_to_buy(account, picks)
        i += 1
        if i % 10 == 0:
            account.get_account_summary()
        if i % 15 == 0:
            account.add_free_cap(100)
            account.save_account()
    account.get_account_summary()


os.chdir(os.path.dirname(os.path.realpath(__file__)))

df = pd.read_csv('sp500.csv')
tickers = df['Symbol'].tolist()
fileName = date.today().isoformat() + 'stock_price.csv'
volFileName = date.today().isoformat() + 'Volume'+'.csv'
fileName = "2022-10-03stock_price.csv"
volFileName = "2022-10-03Volume.csv"
if path.exists(fileName) and path.exists(volFileName):
    data = pd.read_csv(fileName)
    volume = pd.read_csv(volFileName)
else:
    data = download(tickers, '5y')
    volume = data['Volume']
    data = data['Close']
    data.to_csv(fileName)
    volume.to_csv(volFileName)

test_account = Account('Ted Tester', 'tedtester@stockio.com', 5000)
test_wrapper(data, tickers, test_account)






