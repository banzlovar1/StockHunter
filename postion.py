


class Position():
    def __init__(self, ticker, cur_price, amount, date):
        # Create tuple: (<Ticker>, <cur_price>, <shares>, <value>)
        self.ticker = ticker
        self.cur_price = cur_price
        self.shares = round(float(amount / cur_price), 2)
        self.value = round(float(cur_price * self.shares),2)
        self.purchase_date = date
    
    