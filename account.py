import csv


class Account():
    def __init__(self, name, email, value, total_invested, free_capital, change):
        self.name = name
        self.email = email
        self.free_capital = free_capital
        self.value = value
        self.positions = {}
        self.total_invested = total_invested
        self.change = change
    
    def get_postions(self):
        return self.positions
    
    def get_total_invested(self):
        return self.total_invested

    def get_value(self):
        return self.value
    
    def get_positions(self):
        return self.positions
    
    def add_free_cap(self, amount):
        self.free_capital += amount
        self.total_invested += amount
    
    def get_account_summary(self):
        print(f"name={self.name:<20} email={self.email:<20}         free_capital={str(self.free_capital)}      account_value={str(self.value)}     total_invested={str(self.total_invested)}      account_change={str(self.change)}")
        if self.positions:
            print("Ticker               Current Price        Shares               Value                %")
            for pos in self.positions:
                if self.positions[pos]['start_price'] > self.positions[pos]['value']:
                    change = '-' + str((self.positions[pos]['start_price'] - self.positions[pos]['value']) / self.positions[pos]['start_price'])
                else:
                    change = str((self.positions[pos]['value'] - self.positions[pos]['start_price']) / self.positions[pos]['start_price'])
                print(f"{pos:<20} {str(self.positions[pos]['cur_price']):<20} {str(self.positions[pos]['shares']):<20} {str(self.positions[pos]['value']):<20} {change:<20}")

    def buy_position(self, position):
        self.free_capital -= position.value
        if position.ticker in self.positions:
            self.positions[position.ticker]['cur_price'] = position.cur_price
            self.positions[position.ticker]['shares'] += position.shares
            self.positions[position.ticker]['value'] += position.value
            self.positions[position.ticker]['start_price'] += position.value
        else:
            self.positions[position.ticker] = {}
            self.positions[position.ticker]['cur_price'] = position.cur_price
            self.positions[position.ticker]['shares'] = position.shares
            self.positions[position.ticker]['value'] = position.value
            self.positions[position.ticker]['start_price'] = position.value
        
    def sell_position(self, ticker, debug=0):
        if ticker in self.positions:
            self.free_capital += self.positions[ticker]['value']
            if debug:
                print(f"Selling {ticker} giving {self.positions[ticker]['value']} of free cap")
            del self.positions[ticker]
        else:
            print(f"User does not own {ticker}")

    def update_account_value(self):
        stock_value = 0
        for key in self.positions:
            stock_value += self.positions[key]['value']
        self.value = stock_value + self.free_capital
        
        if self.total_invested > self.value:
            self.change = -100 * float((self.total_invested - self.value) / self.total_invested)
        else:
            self.change = 100 * float((self.value - self.total_invested) / self.total_invested)
    
    def update_postion(self, ticker, cur_price):
        self.positions[ticker]['cur_price'] = cur_price
        self.positions[ticker]['value'] = round(self.positions[ticker]['cur_price'] * self.positions[ticker]['shares'], 2)
        self.update_account_value()

    def save_account(self):
        file_name = self.email.split('@')[0] + '_account_position.csv'
        with open(file_name, 'w', newline='') as file:
            for pos in self.positions:
                data = [pos ,self.positions[pos]['start_price'],self.positions[pos]['cur_price'],self.positions[pos]['shares'],self.positions[pos]['value']]
                writer = csv.writer(file)
                writer.writerow(data)
            file.close()
        file_name = self.email.split('@')[0] + '_account_summary.csv'
        with open(file_name, 'w', newline='') as file:
            data = [self.name, self.email, self.value, self.total_invested, self.free_capital, self.change]
            writer = csv.writer(file)
            writer.writerow(data)
            file.close()

    def load_positions(self, pos):
        self.positions[pos[0]] = {}
        self.positions[pos[0]]['start_price'] = float(pos[1])
        self.positions[pos[0]]['cur_price'] = float(pos[2])
        self.positions[pos[0]]['shares'] = float(pos[3])
        self.positions[pos[0]]['value'] = float(pos[4])
       
