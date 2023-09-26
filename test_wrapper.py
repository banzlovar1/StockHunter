# Holds testing code
from back_test import analyze, stocks_to_buy, stocks_to_sell, load_account, download
from postion import Position
from account import Account
import yfinance as yf
import pandas as pd
from os import path
from datetime import date
import os
import numpy as np
from scipy.stats import linregress
import pandas_ta as pta
import csv
import argparse
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import math
from tuning import Tuning
import psutil
import re
import time

def buy_picks(account, picks, stock_price, date):
    if picks:
        for p in picks:
            if account.free_capital > 10:
                pos = Position(p[0], stock_price[p[0]].tolist()[-1], account.free_capital * .1, date)
                account.buy_position(pos)

def sell_picks(account, picks, win, trades, date, tuning=False):
    if picks:
        for p in picks:
            if account.positions[p[0]]['cur_value'] > account.positions[p[0]]['start_value']:
                win += 1
            if tuning:
                with open('sell_pos.csv', 'a', newline='') as file:
                    pos = account.get_position(p[0], p[1], date)
                    writer = csv.writer(file)
                    writer.writerow(pos)
            account.sell_position(p[0])
            trades += 1
    return win, trades


def update_pos(account, stock_data):
    if account.positions:
        for pos in account.positions:
            cur_price = stock_data[pos].tolist()[-1]
            account.update_postion(pos, cur_price)

def test_wrapper(stock_data, tickers, account, stop_loss=.045, momentum_drop=.25, tuning=False, reporting=False):
    # print(f'Begin Test!!!\n\t{account.name} current value : {account.account_value}')
    # Run over 60 data sets for each interval
    i = 0
    rows = stock_data.shape[0]
    win = 0
    trades = 0
    min_params = (0.032, 0.15)
    max_params = (0.06, 0.38)
    while i < rows - 60:
        update_pos(account, stock_data.iloc[i:61+i,:])
        picks = []
        sell = stocks_to_sell(account, stock_data.iloc[i:61+i,:], stop_loss, momentum_drop)
        buy = analyze(stock_data.iloc[i:61+i,:], tickers)
        act_sell = []
        if len(sell):
                for sk in sell:
                    if sk[0] not in buy:
                        act_sell.append(sk)
        win, trades = sell_picks(account, act_sell, win, trades, stock_data.iloc[i:61+i,0].tolist()[-1], tuning)
        buy_picks(account, buy, stock_data.iloc[i:61+i,:], stock_data.iloc[i:61+i,0].tolist()[-1])
        i += 1
        if i % 10 == 0 and reporting:
            account.get_account_summary()
            print(stock_data.iloc[i:61+i,0].tolist()[-1])
        # if i % 15 == 0:
            account.add_free_cap(250)
            account.save_account()
        if tuning and i % 25 == 0: #and i > 21:
            tune = Tuning()
            stop_loss, momentum_drop = tune.tune(data=stock_data.iloc[i-15:61+i,:], model=test_wrapper, tickers=tickers, min_params=min_params, max_params=max_params)
    if reporting:
        account.get_account_summary()
        win_perc = float((win/trades) * 100)
        print("Win Percentage: ", win_perc)
    if not tuning:
        return account.get_value(), stop_loss, momentum_drop
    else:
        return None


if __name__ == "__main__":
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
        data = download(tickers, '10y')
        volume = data['Volume']
        data = data['Open']
        data.to_csv(fileName)
        volume.to_csv(volFileName)

    user = Account('tester', 'tester@gmail.com', 1000, 1000, 1000)
    start_time = time.perf_counter()
    test_wrapper(data, tickers, user, tuning=True, reporting=True)
    finish_time = time.perf_counter()
    print(f"Program finished in {finish_time-start_time} seconds")