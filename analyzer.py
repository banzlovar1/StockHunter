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

stocks = []
end_date = date.today().isoformat()
#end_date = "2020-10-5"  
start_date = (date.today()-timedelta(days=365)).isoformat()
yf.pdr_override()
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

def finder():
    # Load all S&P 500 Tickers
    #os.chdir()
    df = pd.read_csv('sp500.csv')
    tickers = df["Symbol"].tolist()
    counter = 0
    t = time.time()
    #Iterate the tickers
    for ticker in tickers:
        counter = counter+1
        # Download Ticker info
        progress(counter, 505, ticker)
        data = pdr.get_data_yahoo(ticker, period = "1y")#, start = start_date, end = end_date)
        if data.empty:
            pass
            #print("Null")
        else:
            maxCol = data.shape[0]
            minCol = maxCol - 20
            index = list(range(minCol, maxCol))
            # Only care about close data for now
            trend = data['Close'].tolist()
            slope = trenddetector(index, trend[minCol:])
            if slope > .6:
                data = data['Close']
                # Get rolling averages
                short = data.rolling(20).mean()
                short_d = short.last("1D")
                lon = data.rolling(50).mean()
                lon_d = lon.last("1D")
                slope_20MA = trenddetector(index, short[minCol:])
                slope_50MA = trenddetector(index, lon[minCol:])
                if slope_20MA > slope_50MA and lon_d.item() > short_d.item() and data.last("1d").item() < 600:
                #Start filtering out tickers
                # ratio = short_d - lon_d
                # percent = ratio.item() / data.last("1d") *100
                # # add to list if good
                # if abs(percent.item()) < 3 and data.last("1d").item() < 750:
                    #print(counter, " Added: ", ticker)
                    fill = (ticker, round(data.last("1d").item(), 2))
                    stocks.append(fill)
                else:
                    pass
                    #print(counter, " Dropped: ", ticker)
                if counter % 25 == 0:
                    time.sleep(1.5)
                    #print("pause")
            #else:
                #print(counter, " Dropped: ", ticker)
        
       
    print("Time to execute: ", round((time.time() - t)/60, 2), "minutes\n", "Stocks: ", stocks)

def graph():
    for i,j in stocks:
        data = yf.download(i, start=(date.today()-timedelta(days=30)).isoformat(), end=end_date)
        trend = data['Close'].tolist()
        plt.plot(trend, label = i)
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.title("30 Day Stock Info")
    plt.legend()
    plt.show()


finder()
#graph()

