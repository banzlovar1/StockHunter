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
# import robin_stocks.robinhood as rs

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

        williams_r_high = max(ds[-14:])
        williams_r_low = min(ds[-14:])
        if not math.isnan(williams_r_high) or not math.isnan(williams_r_low):
            try:
                williams_r = -100 * ((williams_r_high - ds[-1]) / (williams_r_high - williams_r_low))
            except ZeroDivisionError:
                williams_r = 0
        else:
            williams_r = 0

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
        # elif williams_r < -70 and dataslope > 0:
        #     picks.append((stockList[i],ds[-1],lower_bollinger[-1], rsi))

    # Sort from low to high RSI
    picks.sort(key = lambda x: x[3])
    # Return 5% of the stocks picked up to 10
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

def stochastic_buy(data, stockList):
    picks = []
    for i in range(0, len(stockList)):
        rollingData = data[stockList[i]]
        ds = rollingData.tolist()
        rsi = find_rsi(rollingData).tolist()[-1]
        if rollingData.empty:
            pass
        last_14 = ds[-14:]
        last_3 = ds[-3:]
        K = ((ds[-1] - min(last_14))/(max(last_14)-min(last_14))) * 100
        D = (max(last_3)/min(last_3)) * 100
        if D < 25:
            picks.append((stockList[i],ds[-1], rsi))

def stocks_to_buy(account, picks):
    if account.free_capital > 10: 
        buying = picks[:int(.05*len(picks) if len(picks) < 10 else 10) ]
        for s in buying:
            new_pos = Position(s[0], s[1], (account.free_capital * .1))
            account.buy_position(new_pos)

def stochastic_sell(account, stock_data, stop_loss=.045):
    sell = []
    today_date = date.today()
    if account.positions:
        for pos in account.positions:
            if account.positions[pos]['purchase_date'] != today_date:
                rollingData = stock_data[pos]
                if rollingData.empty:
                    pass
                ds = rollingData.tolist()
                rsi = find_rsi(rollingData).tolist()[-1]
                if rollingData.empty:
                    pass
                last_14 = ds[-14:]
                last_3 = ds[-3:]
                K = ((ds[-1] - min(last_14))/(max(last_14)-min(last_14))) * 100
                D = (max(last_3)/min(last_3)) * 100
                if D > 80 or K > 80:
                    sell.append(pos, "Stochastic limit")
                elif account.positions[pos]['cur_value'] < account.positions[pos]['start_value']:
                    if float((account.positions[pos]['start_value'] - account.positions[pos]['cur_value'])/account.positions[pos]['start_value']) > stop_loss:
                        sell.append((pos, "Greater than 3 percent loss"))
    return sell

def stocks_to_sell(account, stock_data, stop_loss=.045, momentum_drop=.25, williams_r_stop=-40):
    sell = []
    today_date = date.today()
    if account.positions:
        for pos in account.positions:
            if account.positions[pos]['purchase_date'] != today_date:
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
                price_slope = trenddetector(list(range(0,3)), ds[-3:])

                williams_r_high = max(ds[-14:])
                williams_r_low = min(ds[-14:])
                if not math.isnan(williams_r_high) or not math.isnan(williams_r_low):
                    try:
                        williams_r = -100 * ((williams_r_high - ds[-1]) / (williams_r_high - williams_r_low))
                    except ZeroDivisionError:
                        williams_r = 0
                else:
                    williams_r = 0

                # Sell triggers
                # 1) Value of position has dropped to 3% below start
                # 2) 20MA crosses above 5MA
                # 3) 20MA slope drops to lower then .25 (momentum declining)
                # 4) Price has fell below lower bollinger band (sharp decrease in price)
                if account.positions[pos]['cur_value'] < account.positions[pos]['start_value']:
                    if float((account.positions[pos]['start_value'] - account.positions[pos]['cur_value'])/account.positions[pos]['start_value']) > stop_loss:
                        sell.append((pos, "Greater than 3 percent loss"))
                elif lon[-1] > short[-1] and price_slope < 0:
                    sell.append((pos, "20MA greater then 5MA and price sloping down"))
                elif MASlope20 < momentum_drop:
                    sell.append((pos, "20MA sloping down"))
                elif ds[-1] < lower_bollinger[-1]:
                    sell.append((pos, "Price dropped below lower bolinger"))
                elif williams_r > williams_r_stop:
                    sell.append((pos, "Williams R Percent indicates over sold"))
    return sell

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
            # trendList = trend.tolist()
            # Only care about close data for now
            # if (trendList[-1] < 600):# and ():
            watchList.append(tickers[i])
    # return stochastic_buy(data, watchList)
    return bollinger_bands(data, watchList)

def update_postions(account, data):
    if account.positions:
        for pos in account.positions:
            cur_price = data[pos].tolist()[-1]
            account.update_postion(pos, cur_price)

def email(account, sell, buy):
    smtp_server = 'smtp.gmail.com'
    port = 587
    sender_email = 'programtester456@gmail.com'
    password = 'wguthxpikodugqzr'
    reciever_email = account.email
    message = MIMEMultipart('alternative')
    message['Subject'] = f"Account Update for {account.name}'s Account"
    message['From'] = sender_email
    message['To'] = reciever_email
    html = f"""\
    <html>
        <body>
            <h2>Account Summary</h2>
            <h3>Name: {account.name}   Free Capital: {str(account.free_capital)}   Account Value: {str(account.account_value)}   % Change: {str(account.change)}</h3>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Purchase Price</th>
                    <th>Current Price</th>
                    <th>Shares</th>
                    <th>Current Value</th>
                    <th>% Change</th>
                </tr>
    """ 
    for pos in account.positions:
        html += f"""
            <tr>
                <td>{pos}</td>
                <td>{account.positions[pos]['purchase_price']}</td>
                <td>{account.positions[pos]['cur_price']}</td>
                <td>{account.positions[pos]['shares']}</td>
                <td>{account.positions[pos]['cur_value']}</td>
                <td>{str(round(((account.positions[pos]['start_value'] - account.positions[pos]['cur_value']) / account.positions[pos]['start_value']) * -100 if account.positions[pos]['start_value'] > account.positions[pos]['cur_value'] else ((account.positions[pos]['cur_value'] - account.positions[pos]['start_value']) / account.positions[pos]['start_value']) * 100, 2))}</td>
            </tr>
        """
    html += "</table>"

    if len(sell):
        html += """
                <h3>Stocks to Sell</h3>
                <table>
                    <tr>
                    <th>Ticker</th>
                    <th>Current Price</th>
                    <th>% Change</th>
                    </tr>
            """
        for s in sell:
            if account.positions[s[0]]['purchase_price'] != date.today().strftime("%Y-%m-%d"):
                html += f"""
                        <tr>
                            <td>{s[0]}</td>
                            <td>{account.poistions[s[0]]['cur_price']}</td>
                            <td>{str(round(((account.positions[s[0]]['start_value'] - account.positions[s[0]]['cur_value']) / account.positions[s[0]]['start_value']) * -100 if account.positions[s[0]]['start_value'] > account.positions[s[0]]['cur_value'] else ((account.positions[s[0]]['cur_value'] - account.positions[s[0]]['start_value']) / account.positions[s[0]]['start_value']) * 100, 2))}</td>
                        </tr>
                """
        html += "</table>"
    if len(buy):
        html += """
                <h3>Stocks to Buy</h3>
                <table>
                    <tr>
                    <th>Ticker</th>
                    <th>Current Price</th>
                    </tr>
        """
        for b in buy:
            html += f"""
                <tr>
                    <td>{b}</td>
                    <td>{str(get_current_price(b))}</td>
                </tr>
            """
        html += "</table></body></html>"
    mess = MIMEText(html, 'html')
    message.attach(mess)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email,reciever_email,message.as_string())

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
        if parser_name == 'analyze':
            update_postions(account_user, data)
            buy = [i[0] for i in analyze(stock_price_data, tickers)]
            sell = stocks_to_sell(account_user, stock_price_data)
            print("Stocks to sell")
            if len(sell):
                for sk in sell:
                    if sk[0] not in buy:
                        print(sk)
            print("Stocks to buy")
            b = [i for i in buy if i not in account_user.positions]
            print(b)
        if parser_name == 'buy':
            #buy stock wrapper
            today_date = date.today()
            # get_current_price(args.ticker)
            account_user.buy_position(Position(args.ticker, args.purchase_price, args.amount, today_date))
            account_user.get_account_summary()
        elif parser_name == 'sell':
            for tick in args.tickers:
                account_user.sell_position(tick,force=args.force)
            account_user.get_account_summary()
        elif parser_name == 'summary':
            update_postions(account_user, data)
            account_user.get_account_summary()
        elif parser_name == 'email':
            # update_postions(account_user)
            buy = [i[0] for i in analyze(stock_price_data, tickers)]
            sell = stocks_to_sell(account_user, stock_price_data)
            act_sell = []
            if len(sell):
                for sk in sell:
                    if sk[0] not in buy:
                        act_sell.append(sk)
            email(account_user, act_sell, buy)
    else:
        account_user = Account(args.user, args.email, args.capital, args.capital,args.capital)
    account_user.save_account()
    
# To Do:
# 1) Intregrate robinhood login
#   rs.login(username, password)
# 2) Link account to robinhood login (load account info to build account)
#   rs.load_account_profile()
#   rs.build_holdings()
# 3) Automate analyze task
# 4) Send buy and sell calls to RH
#   Send buy in the amount of dollar and not shares rs.orders.order_buy_fractional_by_price(ticker, amnt$)
#       Save order date in csv file
#   Send sell orders to close entire position rs.orders.order_sell_market(ticker, quan)
#       Save sale date and metrics in csv file
# 5) Ensure no day trading is going on

# rs.login(os.environ.get('robinhood_username'), os.environ.get('robinhood_password'))
# print(rs.build_holdings())

# if __name__ == "main":
os.chdir(os.path.dirname(os.path.realpath(__file__)))

df = pd.read_csv('sp500.csv')
tickers = df['Symbol'].tolist()
fileName = date.today().isoformat() + 'stock_price.csv'
volFileName = date.today().isoformat() + 'Volume'+'.csv'
# fileName = "2022-10-03stock_price.csv"
# volFileName = "2022-10-03Volume.csv"
# if path.exists(fileName) and path.exists(volFileName):
#     data = pd.read_csv(fileName)
#     volume = pd.read_csv(volFileName)
# else:
data = download(tickers, '90d')
volume = data['Volume']
data = data['Adj Close']
data.to_csv(fileName)
volume.to_csv(volFileName)


parser = argparse.ArgumentParser(description='Stock picker and account manager')

subparser = parser.add_subparsers(dest='command') 

parser_analyze = subparser.add_parser('analyze', help='Upddate and Analyze account holdings')
parser_analyze.add_argument('-u', '--user', help='Username', required=True)

parser_buy = subparser.add_parser('buy', help="ticker and amount to buy in USD")
parser_buy.add_argument('-u', '--user', help='Username', required=True)
parser_buy.add_argument('-t', '--ticker', help='Stock ticker', required=True)
parser_buy.add_argument('-a', '--amount', type=float, help='amount of stock to buy in USD', required=True)
parser_buy.add_argument('-pp', '--purchase_price', type=float, help='stocks purchase price', required=True)


parser_sell = subparser.add_parser('sell', help='Stock to sell (full close of position)')
parser_sell.add_argument('-u', '--user', help='Username', required=True)
parser_sell.add_argument('-t', '--tickers', nargs='+', help='Stocker ticker to sell', required=True)
parser_sell.add_argument('-f', '--force', action='store_true', help='Force stock sale regardless of day trade warning')

parser_summary = subparser.add_parser('summary', help="Account summary")
parser_summary.add_argument('-u', '--user', help='Username', required=True)

parser_create = subparser.add_parser('create', help='Create account')
parser_create.add_argument('-u', '--user', help='Username', required=True)
parser_create.add_argument('-e', '--email', help='Email', required=True)
parser_create.add_argument('-c', '--capital', help='Capital', required=True)

parser_create = subparser.add_parser('add_capital', help='Add free captial to account')
parser_create.add_argument('-u', '--user', help='Username', required=True)
parser_create.add_argument('-c', '--capital', help='Capital', required=True)

parser_create = subparser.add_parser('email', help='Email account details and analyzed stocks')
parser_create.add_argument('-u', '--user', help='Username', required=True)

args = parser.parse_args()

arg_parse(args.command, args, data, tickers)
# print(args.command)

# Next steps
# Create jenkins server on old laptop and treat as host
# Push my account info into branch and treat as "Trading Branch"
# Jenkins job to run every few hours between trading hours
# Clone the repo into server
# Analyze account, get stocks to buy, give stocks to sell, send in an email
# On my computer or any computer checkout branch, update positions and push to server for Jenkins job to pull and analzye



