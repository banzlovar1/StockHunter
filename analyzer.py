import pandas as pd 
import numpy as np
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

stocks = []
end_date = date.today().isoformat()
#end_date = "2020-10-5"  
start_date = (date.today()-timedelta(days=365)).isoformat()
#yf.pdr_override()
pbar = ProgressBar()

def trenddetector(index, data, order = 1):
    coeffs = np.polyfit(index, list(data), order)
    slope = coeffs[-2]
    return float(slope)

def progress(count, total, status = ''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def analyze(data, tickers, start, end):
    counter = 0
    for i in range(start, end):
        # Download Ticker info
        trend = data['Close'].iloc[:,counter]
        counter = counter+1
        sg.OneLineProgressMeter("Progress Bar", (counter+start), 505, 'single', tickers[i])
        if trend.empty:
            pass
        else:
            maxCol = trend.shape[0]
            minCol = maxCol - 20
            index = list(range(minCol, maxCol))
            trendList = trend.tolist()
            # Only care about close data for now
            slope = trenddetector(index, trendList[minCol:])
            if slope > .6:
                # Get rolling averages
                short = trend.rolling(20).mean()
                short_d = short.last("1D")
                lon = trend.rolling(50).mean()
                lon_d = lon.last("1D")
                slope_20MA = trenddetector(index, short[minCol:])
                slope_50MA = trenddetector(index, lon[minCol:])
                if slope_20MA > slope_50MA and lon_d.item() > short_d.item() and trend.last("1d").item() < 600:
                #Start filtering out tickers
                    fill = (tickers[i])
                    stocks.append(fill)
        
def finder():
    df = pd.read_csv('sp500.csv')
    tickers = df["Symbol"].tolist()
    t = time.time()
    data = yf.download(tickers[:252], period = "1y")#, start = start_date, end = end_date
    analyze(data, tickers, 0, 252)
    data = yf.download(tickers[252:505], period = "1y")#, start = start_date, end = end_date
    analyze(data, tickers, 252, 505)     
    print("Time to execute: ", round((time.time() - t)/60, 2), "minutes\n", "Stocks: ", stocks)

def graph(stock):
    data = yf.download(stock, period = "30d", interval = "90m")
    rollingData = yf.download(stock, period = "60d", interval = "90m")
    data = data['Close']
    rollingData = rollingData['Close']
    trend = data.tolist()
    short = rollingData.rolling(50).mean()
    short = short[149:]
    short = short.tolist()
    lon = rollingData.rolling(100).mean()
    lon = lon[149:]
    lon = lon.tolist()    
    plt.clf()
    plt.plot(trend, label = "20 MA")
    plt.plot(short, label = "5 MA")
    plt.plot(lon)
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
        finder()
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

os.remove("stock.png")
window.close()
