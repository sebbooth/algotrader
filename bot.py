import yfinance as yf
import pandas as pd
import datetime
import schedule
import time
import os
import sys

pd.options.mode.chained_assignment = None

from twilio.rest import Client


ACCOUNT_SID = 'ACCOUNT_SID'
AUTH_TOKEN = 'AUTH_TOKEN'

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def contract(ticker):
    stock = yf.Ticker(ticker)
    dates = stock.options
    return dates[1]

def SMS(ticker, action):
    if (action == 'BUY'):
        expiry = contract(ticker)
        client.messages.create(
            to='PHONENUMBER',
            from_='TWILIOPHONENUMBER',
            body= action + ' ' + expiry + ' ' + ticker
        )
        print(action + ' ' + expiry + ' ' + ticker)
    else:
        client.messages.create(
            to='PHONENUMBER',
            from_='TWILIOPHONENUMBER',
            body= action + ' ' + ticker
        )
        print(action + ' ' + ticker)




class portfolio:
    def __init__(self):
        self.num_positions = 0
        self.positions = {}

    def buy(self, ticker):
        if (self.num_positions >= 4):
            print("Too many open positions to place buy")


        else:
            if (ticker in self.positions):
                if (self.positions[ticker] >= 1):
                    print("Already holding position in " + ticker)

                else:
                    self.positions[ticker] += 1
                    self.num_positions += 1
                    print("Buying: " + ticker)
                    SMS(ticker, 'BUY')
                    ######################### BUY API CALL #################
            else:
                self.positions[ticker] = 1
                self.num_positions += 1
                print("Buying: " + ticker)
                SMS(ticker, 'BUY')
                    ######################### BUY API CALL #################

    def sell(self, ticker):
        if (self.num_positions == 0):
            print("No position in " + ticker + " to sell")

        elif (ticker in self.positions):
            if (self.positions[ticker] == 1):
                self.num_positions -= 1
                self.positions[ticker] -= 1
                print("Selling: " + ticker)
                SMS(ticker, 'SELL')
                ######################## SELL API CALL #################
            else:
                print("No position in " + ticker + " to sell")

        else:
            print("No position in " + ticker + " to sell")


def createDF(ticker_symbol):
    ticker_symbol = ticker_symbol
    period = 100
    interval = '1h'
    end = datetime.datetime.today()
    df = yf.download(ticker_symbol, threads=False, start=datetime.datetime.today() - datetime.timedelta(period), end=end, interval = interval, progress = False)

    df['MA200'] = df['Adj Close'].rolling(window=200).mean()

    df = df.dropna()

    """
    plt.plot(df['Adj Close'])
    plt.plot(df['MA200'])

    plt.show()
    """

    df['Price Change'] = df['Adj Close'].pct_change()

    df = df.dropna()

    df['Upmove'] = df['Price Change'].apply(lambda x: x if x > 0 else 0)
    df['Downmove'] = df['Price Change'].apply(lambda x: abs(x) if x < 0 else 0)

    df['Avg Up'] = df['Upmove'].ewm(span=19).mean()
    df['Avg Down'] = df['Downmove'].ewm(span=19).mean()

    df['RS'] = df['Avg Up']/df['Avg Down']

    df['RSI'] = df['RS'].apply(lambda x: 100-(100/(x+1)))

    df['Sell'] = ''
    ######################## BUY CONDITIONS: ######################################

    df.loc[(df['Adj Close'] > df['MA200']) & (df['RSI'] < 30), 'Buy'] = 'Yes'

    df.loc[(df['Adj Close'] < df['MA200']) | (df['RSI'] > 30), 'Buy'] = ""

    ###############################################################################

    df = df.dropna()
    PnL = []
    Prices = []

    for i in range(len(df) - 12):
        if "Yes" in df['Buy'].iloc[i]:
            Prices.append(df['Open'].iloc[i+1])
            ######################## SELL CONDITIONS: #############################

            for j in range(1,11):
                if df['RSI'].iloc[i + j] > 40:
                    PnL.append( df['Open'].iloc[i+j+1] - df['Open'].iloc[i+1])
                    df['Sell'].iloc[i+j] = 'Yes'
                    break


                if df['RSI'].iloc[i+j] < 40:
                    PnL.append(df['Open'].iloc[i+12] - df['Open'].iloc[i+1])
                    df['Sell'].iloc[i+11] = 'Yes'
                    break

            #######################################################################
    return df

def printData(df):
    pd.set_option('display.max_rows', 4)
    pd.set_option('display.precision', 2)
    print(df.iloc[-4:])


def updateData(tickers):
    data = {}
    for ticker in tickers:
        data[ticker] = createDF(ticker)

    return data

def printAll(data):
    for ticker in tickers:
        print('')
        print(ticker)
        printData(data[ticker])

def checkForBuys(data):
    for ticker in tickers:
        if data[ticker]['Buy'].iloc[-1] == 'Yes':
            print(ticker + ' buy')
            portfolio.buy(ticker)
            ####################### PUT buy() HERE ###############################
"""
        else:
            print(ticker + ' no buy')
"""

def checkForSells(data):
    for ticker in tickers:
        if data[ticker]['Sell'].iloc[-1] == 'Yes':
            print(ticker + ' sell')
            portfolio.sell(ticker)
            ####################### PUT sell() HERE ###############################
"""
        else:
            print(ticker + ' no sell')
"""


tickers = ['MMM', 'CSCO', 'IBM', 'MCD', 'GOOGL', 'EA', 'FB', 'GILD', 'ILMN', 'NFLX', 'SBUX', 'DHR', 'NEE', 'ABC', 'BAX', 'BDX', 'AVGO', 'DRE', 'EXR', 'FTNT', 'GRMN', 'GIS', 'HCA', 'HPQ', 'IDXX']
#tickers = ['AAPL', 'PZZA', 'SNAP', 'IWM', 'FB', 'AA', 'MGM', 'F']
portfolio = portfolio()

########### TESTNG STUFF##########
"""
########## CREATES BUYFREQ DF TO VISUALISE FREQUENCY OF BUY SIGNALS ACROSS ALL TICKERS
data = {}
for ticker in tickers:
    data[ticker] = createDF(ticker)

buyfreq = data['ABC'][:]
buyfreq.drop(buyfreq.columns[0:16], axis=1, inplace=True)

for ticker in tickers:
    colname = ticker+' buy'
    buyfreq[colname] = data[ticker]['Buy'].values

print("ok")
"""
 ########## LOOOP ###############

#"""

for i in range(1, len(sys.argv)):
    portfolio.positions[sys.argv[i]] = 1

data = {}
#try:
for ticker in tickers:
    data[ticker] = createDF(ticker)

#except:
#    print("*****************\n" * 4)
#    print("why is it doing this\n" * 4)
#    print("*****************\n" * 4)

now = datetime.datetime.now()
now = now.replace(microsecond=0)

numpostions = portfolio.positions
checkForBuys(data)
checkForSells(data)
os.system('cls||clear')

printAll(data)
print(' ')
print(' ')
print("Current time:")
print(now)
print("Portfolio positions: " + str(portfolio.positions))



if numpostions == portfolio.positions:
    print("NO BUYS OR SELLS")

def job():
    try:
        errors += 0
    except:
        errors = 0
    try:
        data = {}
        
        for ticker in tickers:
            data[ticker] = createDF(ticker)

        now = datetime.datetime.now()
        now = now.replace(microsecond=0)

        numpostions = portfolio.positions
        checkForBuys(data)
        checkForSells(data)
        os.system('cls||clear')

        printAll(data)
        print(' ')
        print(' ')
        print("Current time:")
        print(now)
        print("Portfolio positions: " + str(portfolio.positions))
        print("errors: " + str(errors))



        if numpostions == portfolio.positions:
            print("NO BUYS OR SELLS")
        errors = 0
    except:
        errors += 1
        print("*****************\n" *3 )
        print("error", str(errors), "yikes\n")
        print("*****************\n" *3 )
        
schedule.every(120).seconds.do(job)


while 1:
    schedule.run_pending()
    time.sleep(1)


#"""
