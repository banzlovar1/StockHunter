# Holds testing code

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