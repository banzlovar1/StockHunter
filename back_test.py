from distutils.command import check
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
import csv
import argparse

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
    return picks[:int(.05*len(picks) if len(picks) < 10 else 10)]

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
        buying = picks[:int(.05*len(picks) if len(picks) < 10 else 10) ]
        for s in buying:
            new_pos = Position(s[0], s[1], (account.free_capital * .1))
            account.buy_position(new_pos)

def stocks_to_sell(account, stock_data):
    sell = []
    if account.positions:
        for pos in account.positions:
            rollingData = stock_data[pos]
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
            if account.positions[pos]['cur_value'] < account.positions[pos]['start_value']:
                if float((account.positions[pos]['start_value'] - account.positions[pos]['cur_value'])/account.positions[pos]['start_value']) > .03:
                    sell.append(pos)
            elif lon[-1] > short[-1]:
                sell.append(pos)
            elif MASlope20 < 0.25:
                sell.append(pos)
    return sell
        
        # field_names = ['Ticker', 'Start_Value', 'Sale_Value', 'Account_Value', 'Total_Invested']
        # for ticker in sell:
        #     row = {'Ticker': ticker, 'Start_Value': account.positions[ticker]['start_price'], 'Sale_Value': account.positions[ticker]['value'], 'Account_Value': account.get_value(), 'Total_Invested': account.get_total_invested()}
        #     account.sell_position(ticker)
        #     with open('sales_test.csv', 'a', newline='') as f_object:
        #         dictWriter_obj = DictWriter(f_object, fieldnames=field_names)
        #         dictWriter_obj.writerow(row)
        #         f_object.close()


def analyze(data, tickers):
    counter = 0
    watchList = []
    for i in range(0, len(tickers)):
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

def update_postions(account):
    # define selling positions and updating account and positions here
    # conditions
    #   1) Lost 5% on trade
    #   2) Gained 10% on trade
    #   3) Stock goes below 20 MA (crossover specific)
    if account.positions:
        for pos in account.positions:
            cur_price = get_current_price(pos)
            account.update_postion(pos, cur_price)

# def test_wrapper(stock_data, tickers, account):
#     print(f'Begin Test!!!\n\t{account.name} current value : {account.value}')
#     # Run over 60 data sets for each interval
#     i = 0
#     rows = data.shape[0]
#     while i < rows - 60:
#         picks = []
#         check_postions(data.iloc[i:61+i,:], account)
#         picks = analyze(data.iloc[i:61+i,:], tickers, len(tickers))
#         stocks_to_buy(account, picks)
#         i += 1
#         if i % 10 == 0:
#             account.get_account_summary()
#         if i % 15 == 0:
#             account.add_free_cap(100)
#             account.save_account()
#     account.get_account_summary()

def get_current_price(ticker):
    ticker_info = yf.Ticker(ticker)
    return ticker_info.info['currentPrice']

def load_account(name):
    acc = []
    with open(name+'_account_summary.csv') as file: 
        reader = csv.reader(file)
        for row in reader:
            acc.append(row)
    user_account = Account(acc[0][0],acc[0][1],float(acc[0][2]),float(acc[0][3]),float(acc[0][4]),float(acc[0][5]))
    pos = []
    if os.path.exists(name+'_account_position.csv'):
        if os.stat(name+'_account_position.csv').st_size != 0:
            with open(name+'_account_position.csv', 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    pos.append(row)
            for p in pos:
                user_account.load_positions(p)
    print(f"{name} Account has been successfully loaded\n")
    # user_account.get_account_summary()
    return user_account

def arg_parse(parser_name, args, stock_price_data, tickers):
    if parser_name != 'create':
        user = args.user
        # load account
        account_user = load_account(user)
        # update account positions
        update_postions(account_user)
        if parser_name == 'analyze':
            buy = [i[0] for i in analyze(stock_price_data, tickers)]
            sell = stocks_to_sell(account_user, stock_price_data)
            print("Stocks to sell")
            if len(sell):
                for sk in sell:
                    if sk not in buy:
                        print(sk)
            print("Stocks to buy")
            b = [i for i in buy if i not in account_user.positions]
            print(b)
        if parser_name == 'buy':
            #buy stock wrapper
            get_current_price(args.ticker)
            account_user.buy_position(Position(args.ticker, get_current_price(args.ticker), args.amount))
            account_user.get_account_summary()
        elif parser_name == 'sell':
            account_user.sell_position(args.ticker)
        elif parser_name == 'summary':
            account_user.get_account_summary()
    else:
        account_user = Account(args.user, args.email, args.capital, args.capital,args.capital)
    account_user.save_account()
    
os.chdir(os.path.dirname(os.path.realpath(__file__)))

df = pd.read_csv('sp500.csv')
tickers = df['Symbol'].tolist()
fileName = date.today().isoformat() + 'stock_price.csv'
volFileName = date.today().isoformat() + 'Volume'+'.csv'
# fileName = "2022-10-03stock_price.csv"
# volFileName = "2022-10-03Volume.csv"
if path.exists(fileName) and path.exists(volFileName):
    data = pd.read_csv(fileName)
    volume = pd.read_csv(volFileName)
else:
    data = download(tickers, '3y')
    volume = data['Volume']
    data = data['Open']
    data.to_csv(fileName)
    volume.to_csv(volFileName)

# df = data.iloc[-60:,:]
# user = load_account('banzlovar')
# buy = analyze(df,tickers, len(tickers))
# print('Stocks to buy')
# for stock in buy:
#     print(stock[0])
# sell = check_postions(df, user)
# user.get_account_summary()
# print('Stocks to Sell')
# for s in sell:
#     if s not in map(lambda x: x[0], buy):
#         print(s)
# user.save_account()

parser = argparse.ArgumentParser(description='Stock picker and account manager')

subparser = parser.add_subparsers(dest='command')

parser_analyze = subparser.add_parser('analyze', help='Upddate and Analyze account holdings')
parser_analyze.add_argument('-u', '--user', help='Username', required=True)

parser_buy = subparser.add_parser('buy', help="ticker and amount to buy in USD")
parser_buy.add_argument('-u', '--user', help='Username', required=True)
parser_buy.add_argument('-t', '--ticker', help='Stock ticker', required=True)
parser_buy.add_argument('-a', '--amount', type=float, help='amount of stock to buy in USD', required=True)

parser_sell = subparser.add_parser('sell', help='Stock to sell (full close of position)')
parser_sell.add_argument('-u', '--user', help='Username', required=True)
parser_sell.add_argument('-t', '--ticker', help='Stocker ticker to sell', required=True)

parser_summary = subparser.add_parser('summary', help="Account summary")
parser_summary.add_argument('-u', '--user', help='Username', required=True)

parser_create = subparser.add_parser('create', help='Create account')
parser_create.add_argument('-u', '--user', help='Username', required=True)
parser_create.add_argument('-e', '--email', help='Email', required=True)
parser_create.add_argument('-c', '--capital', help='Capital', required=True)

args = parser.parse_args()

arg_parse(args.command, args, data, tickers)
# print(args.command)





