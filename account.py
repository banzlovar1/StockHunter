import csv
from datetime import date, datetime

class Account():
    def __init__(self, name, email, account_value, total_invested, free_capital, change=0):
        self.name = name
        self.email = email
        self.free_capital = free_capital
        self.account_value = account_value
        self.positions = {}
        self.total_invested = total_invested
        self.change = change
    
    def get_postions(self):
        return self.positions
    
    def get_total_invested(self):
        return self.total_invested

    def get_value(self):
        return self.account_value
    
    def get_position(self, ticker, reason, date):
        return [ticker, self.positions[ticker]['purchase_date'], date, self.positions[ticker]['shares'], self.positions[ticker]['start_value'], self.positions[ticker]['cur_value'], reason]
    
    def add_free_cap(self, amount):
        self.free_capital += amount
        self.total_invested += amount
    
    def get_account_summary(self):
        print(f"name={self.name:<20} email={self.email:<20}         free_capital={str(self.free_capital)}      account_value={str(self.account_value)}     total_invested={str(self.total_invested)}      account_change={str(self.change)}")
        if self.positions:
            print("Ticker               Purchase Price       Current Price        Shares               Current Value        %")
            for pos in self.positions:
                if self.positions[pos]['start_value'] > self.positions[pos]['cur_value']:
                    change = '-' + str(round(((self.positions[pos]['start_value'] - self.positions[pos]['cur_value']) / self.positions[pos]['start_value']) * 100, 2))
                else:
                    change = str(round(((self.positions[pos]['cur_value'] - self.positions[pos]['start_value']) / self.positions[pos]['start_value']) * 100, 2))
                print(f"{pos:<20} {str(self.positions[pos]['purchase_price']):<20} {str(self.positions[pos]['cur_price']):<20} {str(self.positions[pos]['shares']):<20} {str(self.positions[pos]['cur_value']):<20} {change:<20}")

    def buy_position(self, position):
        self.free_capital -= position.value
        if position.ticker in self.positions:
            self.positions[position.ticker]['cur_price'] = position.cur_price
            self.positions[position.ticker]['shares'] += position.shares
            self.positions[position.ticker]['cur_value'] += position.value
            self.positions[position.ticker]['start_value'] += position.value
            # Average out purchase price for repurchase
            self.positions[position.ticker]['purchase_price'] = (self.positions[position.ticker]['purchase_price'] + position.cur_price) / 2.0
            self.positions[position.ticker]['purchase_date'] = position.purchase_date
        else:
            self.positions[position.ticker] = {}
            self.positions[position.ticker]['cur_price'] = position.cur_price
            self.positions[position.ticker]['shares'] = position.shares
            self.positions[position.ticker]['cur_value'] = position.value
            self.positions[position.ticker]['start_value'] = position.value
            self.positions[position.ticker]['purchase_price'] = position.cur_price
            self.positions[position.ticker]['purchase_date'] = position.purchase_date
        
    def sell_position(self, ticker, debug=0, force=0):
        if ticker in self.positions:
            if self.positions[ticker]['purchase_date'] != date.today().strftime("%Y-%m-%d") or force:
                self.free_capital += self.positions[ticker]['cur_value']
                if debug:
                    print(f"Selling {ticker} giving {self.positions[ticker]['cur_value']} of free cap")
                del self.positions[ticker]
            else:
                print("Day Trade Warning: Cannot sell position")
        else:
            print(f"User does not own {ticker}")

    def update_account_value(self):
        stock_value = 0
        for key in self.positions:
            stock_value += self.positions[key]['cur_value']
        self.account_value = stock_value + self.free_capital
        
        if self.total_invested > self.account_value:
            self.change = -100 * float((self.total_invested - self.account_value) / self.total_invested)
        else:
            self.change = 100 * float((self.account_value - self.total_invested) / self.total_invested)
    
    def update_postion(self, ticker, cur_price):
        self.positions[ticker]['cur_price'] = cur_price
        self.positions[ticker]['cur_value'] = round(self.positions[ticker]['cur_price'] * self.positions[ticker]['shares'], 2)
        self.update_account_value()

    def save_account(self):
        file_name = self.email.split('@')[0] + '_account_position.csv'
        with open(file_name, 'w', newline='') as file:
            for pos in self.positions:
                data = [pos, self.positions[pos]['purchase_price'],self.positions[pos]['cur_price'],self.positions[pos]['start_value'],self.positions[pos]['shares'],self.positions[pos]['cur_value'],self.positions[pos]['purchase_date']]
                writer = csv.writer(file)
                writer.writerow(data)
            file.close()
        file_name = self.email.split('@')[0] + '_account_summary.csv'
        with open(file_name, 'w', newline='') as file:
            data = [self.name, self.email, self.account_value, self.total_invested, self.free_capital, self.change]
            writer = csv.writer(file)
            writer.writerow(data)
            file.close()

    def load_positions(self, pos):
        self.positions[pos[0]] = {}
        self.positions[pos[0]]['purchase_price'] = float(pos[1])
        self.positions[pos[0]]['cur_price'] = float(pos[2])
        self.positions[pos[0]]['start_value'] = float(pos[3])
        self.positions[pos[0]]['shares'] = float(pos[4])
        self.positions[pos[0]]['cur_value'] = float(pos[5])
        self.positions[pos[0]]['purchase_date'] = pos[6]
       
