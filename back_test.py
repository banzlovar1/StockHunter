from postion import Position
from account import Account
from analyzer import analyze


def check_postions(stock_data, account):
    # define selling positions and updating account and positions here
    # conditions
    #   1) Lost 5% on trade
    #   2) Gained 10% on trade
    #   3) Stock goes below 20 MA (crossover specific)
    print('Update account')

    print(f'\n\n{account.name} current summary')
    for pos in account.positions:
        print(f'{pos.ticker} : {pos.shares} : {pos.value}')


def test_wrapper(stock_data, account):
    print(f'Begin Test!!!\n\t{account.name} current value : {account.capital}')
    # Run over 60 data sets for each interval


test_pos = Position('TSLA', 45.50, 100)
test_account = Account('Ted Tester', 'tedtester@stockio.com', 1000)
test_account.get_account_summary()
test_account.sell_postion('TSLA')
test_account.buy_position(test_pos)
test_account.get_account_summary()
test_account.update_postion('TSLA', 50.55)
test_account.get_account_summary()
test_account.sell_postion('TSLA')
test_account.get_account_summary()




