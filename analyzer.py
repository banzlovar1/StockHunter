from numpy.core.numeric import roll
import pandas as pd 
import numpy as np
from statistics import mean
from datetime import date, timedelta
import matplotlib.pyplot as plt
from os import path
import yfinance as yf
import time
from pandas_datareader import data as pdr
from progressbar import ProgressBar
from tqdm import tqdm
import sys
import PySimpleGUI as sg
import os.path
import csv
import func_timeout as fun
from scipy.stats import linregress
import os

os.chdir(os.path.dirname(os.path.realpath(__file__)))

stocks = []
end_date = date.today().isoformat()
start='2020-8-3'
pbar = ProgressBar()


# Finds slopes given a list of data
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

# Depending on the test, return list of stocks
def isTrend(data, stockList, choice):
    returnList = []
    for i in range(0, len(stockList)):
        sg.OneLineProgressMeter("Progress Bar", i, (len(stockList)-1), 'single', stockList[i])
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
        

        index = list(range(0, 3))

        shortslope = trenddetector(index, short[-3:])
        dataslope = trenddetector(index, ds[-3:])

        if choice == 1:
            if crossOver(lon, short, rollingData) and shortslope > 0.3 and dataslope > 0:
                returnList.append(stockList[i])
        elif choice == 2:
            if  breakThrough(rollingData, short) and dataslope > 0 and shortslope > 0:
                returnList.append(stockList[i])
        else:
            if ds[-1] < lon[-1] and ds[-1] > lower_bollinger[-1] and short[-1] > lower_bollinger[-1]:
                short_ma_close = float((short[-1] - lower_bollinger[-1]) / short[-1]) * 100.0
                gap = float((ds[-1] - lower_bollinger[-1]) / ds[-1]) * 100.0
                if gap < 1.2 and short_ma_close > 2:
                    returnList.append((stockList[i], ds[-1], lower_bollinger[-1], upper_bollinger[-1]))

    return returnList

# Filters stocks if no data or above price threshold
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
    return isTrend(data, watchList, choice)
    
#Wrapper function for stock analysis      
def finder(data, choice):
    stocks = analyze(data, tickers, len(tickers), choice)
    return stocks

# Stock Download ticker
def download(stock):
    data = yf.download(stock, period = "60d")
    return data

# Plot a graph and save as png to open in GUI
def graph(stock, data, vol):
    if data.empty:
        pass
    else:
        rollingData = data
        da = data[29:(len(data)-1)]
        short = rollingData.rolling(5).mean()
        short = short[29:(len(short)-1)]
        lon = rollingData.rolling(20).mean()
        lon = lon[29:(len(lon)-1)]

        std = rollingData.rolling(20).std()
        upper_bollinger = lon + std * 2
        upper_bollinger = upper_bollinger[29:(len(upper_bollinger)-1)]
        lower_bollinger = lon - std * 2
        lower_bollinger = lower_bollinger[29:(len(lower_bollinger)-1)]

        fig = plt.figure(figsize=(6,4))
        fig.clf()
        fig.add_subplot(2,1,1)
        # Plot stock closing Prices
        plt.plot(da)
        d = da.tolist()
        plt.annotate(round(d[-1],2), xy =(60, data[-1:]))
        # Plot 5 day SMA
        plt.plot(short, label = "5 MA")
        s = short.tolist()
        plt.annotate(round(s[-1],2), xy =(60, short[-1:]))
        # # Plot 20 day SMA
        plt.plot(lon, label = "20 MA")
        # l = lon.tolist()
        # plt.annotate(round(l[-1],2), xy =(60, lon[-1:]))

        plt.plot(lower_bollinger, label='lower bollinger')
        plt.plot(upper_bollinger, label='upper bollinger')

        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        title = "30 Day Stock Info: " +stock
        plt.title(title)
        plt.xticks(rotation=60)
        # Volume Plot
        # fig.add_subplot(2,1,2)
        # vol=vol[29:len(vol)-1]
        # plt.bar(vol.index, vol, color='Green')
        # plt.xticks(rotation=60)
        plt.savefig("stock.png")

def positions(pos):
    g = []
    for row in pos.index:
        st = pos['Stock'][row]
        st = "{:<10}".format(st)
        en = str(pos['Entry'][row])
        en = "{:<15}".format(en)
        cr = str(pos['Current'][row])
        cr = "{:<15}".format(cr)
        qu = str(pos['Quan'][row])
        qu = "{:<12}".format(qu)
        gn = str(pos['Gain'][row])
        gn = "{:<12}".format(gn)
        s = st+en+cr+qu+gn
        if ((pos['Current'][row] / pos['Entry'][row]) - 1) < -.05:
            s = s+"Sell"
        else:
            s = s+"Hold"
        g.append(s)
    return g

def addPosition(data, ps, stock, price, quan):
    print("ADD")
    gain = (data[60]* quan) - (price*quan)
    newrow = {'Date':date.today().isoformat(), 'Stock':stock, 'Entry':price,
                'Current':round(data[60],2), 'Quan':quan, 'Gain':round(gain, 2)}
    ps = ps.append(newrow, ignore_index=True)
    # print(ps)
    return ps

def updatePos(data, ps):
    for row in ps.index:
        d = data[ps['Stock'][row]]
        d = round(d[60], 2)
        ps['Current'][row] = d
        newGain = round((ps['Current'][row] * ps['Quan'][row]) - (ps['Entry'][row] * ps['Quan'][row]), 2)
        ps['Gain'][row] = newGain
    return ps


# ######### Pre-Processing ##########################
# df = pd.read_csv('sp500.csv')
# tickers = df['Symbol'].tolist()
# fileName = date.today().isoformat() + 'stock_price.csv'
# volFileName = date.today().isoformat() + 'Volume'+'.csv'
# # fileName = "B:\\StockHunter\\V1\\2020-12-03.csv"
# # volFileName = "B:\\StockHunter\\V1\\2020-12-03Volume.csv"
# if path.exists(fileName) and path.exists(volFileName):
#     data = pd.read_csv(fileName)
#     volume = pd.read_csv(volFileName)
# else:
#     data = download(tickers)
#     volume = data['Volume']
#     data = data['Close']
#     data.to_csv(fileName)
#     volume.to_csv(volFileName)

# pos = []
# ps = pd.DataFrame()
# try:
#     ps = pd.read_csv('position.csv')
#     ps = updatePos(data, ps)
#     pos = positions(ps)
# except:
#     pass
# ######### Pre-Processing ##########################


# sg.theme('Dark')
# ################ Tab 1 Layout #########################
# # First the window layout in 2 columns

# file_list_column = [
#     [sg.Button("Calculate", key ="-CALCULATE-"),
#     sg.Text("")],

#     [sg.Checkbox('Crossing Moving Average', default = True, key = "-CMA-"),
#     sg.Checkbox('Breakthrough', key= "-BREAKTHROUGH-")],

#     [sg.Listbox(values=[], enable_events=True, size=(40, 20), key="-STOCK LIST-")]
# ]

# # For now will only show the name of the file that was chosen
# image_viewer_column = [
#     [sg.Text("Choose a Stock from the List on the Left:")],

#     [sg.Image(key="-IMAGE-")],
# ]

# # ----- Full layout -----
# t1layout = [
#     [sg.Column(file_list_column),
#     sg.VSeperator(),
#     sg.Column(image_viewer_column)]
# ]
# ########### Tab 1 ###################################
# headings = ps.head()
# ########### Tab 2 ###################################
# tab2 = [[sg.Text("Enter Stock, Purchase Price, and Quantity")],
#     [sg.Button("Add", key ="-ADD-"), 
#     sg.Text("Stock"), sg.InputText(key = "-S-", size=(12,1), do_not_clear=False),
#     sg.Text("Price"), sg.InputText(key = "-P-", size=(12,1), do_not_clear=False), 
#     sg.Text("Quantity"), sg.InputText(key = "-Q-", size=(12,1), do_not_clear=False)],

#     [sg.Text("Stock     Entry      Current      Quantity    Gain")],

#     [sg.Listbox(values=pos, enable_events=True, size=(80, 20), key="-POSITIONS-")]
#     ]

# ########### Tab 2 ###################################

# layout = [[sg.TabGroup([[sg.Tab('Stocki', t1layout), sg.Tab('Portfolio', tab2)]])]]

# window = sg.Window("Stocki", layout)

# ######### Window Loop #############################
# while True:
#     event, values = window.read()
#     if event == "Exit" or event == sg.WIN_CLOSED:
#         break
#     # Folder name was filled in, make a list of files in the folder
#     if event == "-CALCULATE-":
#         if values["-BREAKTHROUGH-"] == True and values["-CMA-"] == True:
#             pass
#         elif values["-CMA-"] == True:
#             window["-IMAGE-"].update()
#             stocks = finder(data, 3)
#             window["-STOCK LIST-"].update(stocks)
#             print("CMA")
#         elif values["-BREAKTHROUGH-"] == True:
#             window["-IMAGE-"].update()
#             stocks = finder(data, 2)
#             window["-STOCK LIST-"].update(stocks)
#             print("BT")
#     elif event == "-STOCK LIST-":  # A file was chosen from the listbox
#         try:
#             stock = values["-STOCK LIST-"][0]
#             graph(stock, data[stock], volume[stock])  
#             window["-IMAGE-"].update(filename="stock.png")
#         except:
#             pass
#     elif event == "-ADD-":
#         try:
#             ps = addPosition(data[values["-S-"]], ps, values["-S-"], float(values["-P-"]), int(values["-Q-"]))
#             pos = positions(ps)
#             ps.to_csv('position.csv')
#             window["-POSITIONS-"].update(pos)
#         except:
#             pass

# try:
#     os.remove("stock.png")
# except:
#     pass
# window.close()

# ######### Window Loop #############################

