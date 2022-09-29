


class Account():
    def __init__(self, name, email, capital):
        self.name = name
        self.email = email
        self.free_capital = capital
        self.value = capital
        self.positions = {}
    
    def get_postions(self):
        return self.positions

    def get_value(self):
        return self.value
    
    def get_positions(self):
        return self.positions
    
    def get_account_summary(self):
        print(f"name={self.name:<20} email={self.email:<20}         free_capital={str(self.free_capital)}      account_value={str(self.value)}")
        if self.positions:
            print("Ticker                Current Price       Shares          Value")
            for pos in self.positions:
                print(f"{pos:<20} {str(self.positions[pos]['cur_price']):<20} {str(self.positions[pos]['shares']):<20} {str(self.positions[pos]['value']):<20}")

    def buy_position(self, position):
        self.free_capital -= position.value
        if position.ticker in self.positions:
            self.positions[position.ticker]['cur_price'] = position.cur_price
            self.positions[position.ticker]['shares'] += position.shares
            self.positions[position.ticker]['value'] += position.value
        else:
            self.positions[position.ticker] = {}
            self.positions[position.ticker]['cur_price'] = position.cur_price
            self.positions[position.ticker]['shares'] = position.shares
            self.positions[position.ticker]['value'] = position.value
        
    def sell_postion(self, ticker):
        if ticker in self.positions:
            self.free_capital += self.positions[ticker]['value']
            print(f"Selling {ticker} giving {self.positions[ticker]['value']} of free cap")
            del self.positions[ticker]
        else:
            print(f"User does not own {ticker}")

    def update_account_value(self):
        stock_value = 0
        for key in self.positions:
            stock_value += self.positions[key]['value']
        self.value = stock_value + self.free_capital
    
    def update_postion(self, ticker, cur_price):
        self.positions[ticker]['cur_price'] = cur_price
        self.positions[ticker]['value'] = round(self.positions[ticker]['cur_price'] * self.positions[ticker]['shares'], 2)
        self.update_account_value()