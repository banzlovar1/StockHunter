import pandas as pd 
import numpy as np
from statistics import mean
from datetime import date, timedelta
import matplotlib.pyplot as plt
import os
import yfinance as yf
import time
from pandas_datareader import data as pdr
from progressbar import ProgressBar
from tqdm import tqdm
import sys
import PySimpleGUI as sg
import os.path
import csv

stocks = []
#end_date = date.today().isoformat()
end_date = "2020-10-5"  
start_date = (date.today()-timedelta(days=365)).isoformat()
#yf.pdr_override()
pbar = ProgressBar()

def trenddetector(index, data, order = 1):
    coeffs = np.polyfit(index, list(data), order)
    slope = coeffs[-2]
    return float(slope)

def isTrend(data, stockList):
    returnList = []
    for i in range(0, len(stockList)):
        rollingData = data[stockList[i]]
        if rollingData.empty:
            pass
        #print(rollingData.head())
        short = rollingData.rolling(5).mean()
        short = short.tolist()
        lon = rollingData.rolling(20).mean()
        lon = lon.tolist()

        index = list(range(0, 3))

        slope = trenddetector(index, short[-3:])
        
        if lon[-1] > short[-1] and (short[-1]/lon[-1] > .995) and slope > 0:
            returnList.append(stockList[i])
            print("added: ", stockList[i])
            print(short[-1])
            print(lon[-1])
    return returnList

def progress(count, total, status = ''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def analyze(data, tickers, start, end):
    counter = 0
    watchList = []
    for i in range(start, end):
        # Download Ticker info
        trend = data[tickers[i]]
        counter = counter+1
        #sg.OneLineProgressMeter("Progress Bar", (counter+start), 505, 'single', tickers[i])
        if trend.empty:
            pass
        else:
            trendList = trend.tolist()
            # Only care about close data for now
            if (trendList[-1] < 600):# and ():
                watchList.append(tickers[i])
    return isTrend(data, watchList)
    
        
def finder():
    firstList = []
    secondList = []
    df = pd.read_csv('sp500.csv')
    tickers = df['Symbol'].tolist()
    t = time.time()
    # data = yf.download(tickers[:252], period = "1y")#, start = start_date, end = end_date
    # data = data['Close']
    # firstList = analyze(data, tickers, 0, 252)
    data = yf.download(tickers, period = "60d")#, start = start_date, end = end_date
    data = data['Close']
    secondList = analyze(data, tickers, 0, 505)
    stocks = firstList + secondList     
    print("Time to execute: ", round((time.time() - t)/60, 2), "minutes\n", "Stocks: ", stocks)
    return stocks

def graph(stock):
    data = yf.download(stock, period = "30d")
    rollingData = yf.download(stock, period = "60d")
    data = data['Close']
    rollingData = rollingData['Close']
    trend = data.tolist()
    short = rollingData.rolling(5).mean()
    short = short[29:]
    short = short.tolist()
    lon = rollingData.rolling(20).mean()
    lon = lon[29:]
    lon = lon.tolist()    
    plt.clf()
    plt.plot(trend)
    plt.plot(short, label = "5 MA")
    plt.plot(lon, label = "20 MA")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    title = "30 Day Stock Info: " +stock
    plt.title(title)
    plt.savefig("stock.png")


# First the window layout in 2 columns

file_list_column = [
    [
        # sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.Button("Calculate", key ="-CALCULATE-"),
        sg.Text("")
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-STOCK LIST-"
        )
    ],
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.Text("Choose an Stock From the List on the Left:")],
    [sg.Image(key="-IMAGE-")],
    [sg.Text(size=(20, 1), key="-TOUT-")],
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(image_viewer_column),
    ]
]


window = sg.Window("Stock Finder", layout)

# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == "-CALCULATE-":
        stocks = finder()
        window["-STOCK LIST-"].update(stocks)
    elif event == "-STOCK LIST-":  # A file was chosen from the listbox
        try:
            stock = values["-STOCK LIST-"][0]
            print(stock)      
            graph(stock)  
            window["-TOUT-"].update("stock.png")
            window["-IMAGE-"].update(filename="stock.png")

        except:
            pass

try:
    os.remove("stock.png")
except:
    pass
window.close()

