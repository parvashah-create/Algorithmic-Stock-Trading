
#importing dependencies
import time
import ks_api_client
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
from ks_api_client import ks_api

# Assigning Variables
# I am using Kotak Api to perform trades in the stock market
access_token = "" # your access token
userid = "" # your user id
consumer_key = "" # your consumer key
app_id = "" # your app id
access_code = "" # your access code
password = "" # your password

#For using sandbox environment use host as https://sbx.kotaksecurities.com/apim
# Kotak API query to connect to the client
client = ks_api.KSTradeApi(access_token = access_token, userid = userid,
                          consumer_key = consumer_key , ip = "127.0.0.1",
                          app_id = app_id)

# Get session for user
client.login(password = password )

# #Generated session token
client.session_2fa(access_code = access_code )
print("Connection to the Client Successful!")


# Trading Ticker Information
symbol = 'IRCTC.NS'
instrument_token = 2182
exchange = 'NSE'
period = '1d'
interval = '1m'
quantity = 2
std_mul = 2 #standard deviation multiple
tp_sd = 2  #take profit standard deviation
sl_sd = 1.5  #stop loss standard deviation



# Function to place a market order
def market_order(instrument_token,order_type,quantity,trigger_price,transaction_type,price,tag):
    order_sent = client.place_order(order_type = order_type, instrument_token = instrument_token,
                   transaction_type = transaction_type, quantity = quantity, price = price,
                   disclosed_quantity = 0, trigger_price=trigger_price,
                   validity = "GFD", variety = "REGULAR", tag = tag)
    print(order_sent)

    return order_sent

# Getting BUY & SELL Signals
def get_signal():
    # Getting Historical Data
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False)
    # Take the last 20 readings
    df = df.tail(20)
    # Convert DataFrame Index to DateTime
    df.reset_index(level=0, inplace=True)
    # Rename columns
    df = df.rename(columns={'Datetime':'time','Open':'open', 'Close':'close', 'High':'high','Low':'low','Volume':'tick_volume'})

    # calculate bollinger bands

    # calculate sma
    sma = df['close'].mean()

    # calculate standard deviation
    std = df['close'].std()

    # calculate lower band
    lower_band = sma - std_mul * std

    # calculate upper band
    upper_band = sma + std_mul * std

    #last close price
    last_close_price = df.iloc[-1]['close']

    # finding signal
    if last_close_price < lower_band:
        return 'BUY', std
    elif last_close_price > upper_band:
        return 'SELL', std
    else:
        return [None, None]

#Conditions to run this loop perfectly and avoid any errors:
#Can't keep changing the instrument token again and again, we need to stick to one token at a time
#Can only run this program 20min after market open so 9:35AM

while True:
    # Check if there are no open trades
    if len(client.positions(position_type="OPEN")['Success']) == 0:
        bs_position = 0
    # If trading positions open then assign variable as net quantity traded
    else:
        df = pd.DataFrame(client.positions(position_type = "OPEN")['Success'])
        bs_position = df.loc[df['instrumentToken'] == instrument_token]["netTrdQtyLot"].item()


    if bs_position == 0:
        while True:
            Signal, std_dev = get_signal()
            if Signal == "BUY":
                last_price = float(client.quote(instrument_token, quote_type='LTP')['success'][0]['lastPrice'])
                tp_price = round((last_price + tp_sd * std_dev) / 0.05) * 0.05
                sl_price = round((last_price - sl_sd * std_dev) / 0.05) * 0.05
                order_info = market_order(instrument_token=instrument_token, order_type="MIS", quantity=quantity, trigger_price=0, transaction_type="BUY", price=0, tag="Buy_Order")
                break
            elif Signal == "SELL":
                last_price = float(client.quote(instrument_token, quote_type='LTP')['success'][0]['lastPrice'])
                tp_price = round((last_price - tp_sd * std_dev) / 0.05) * 0.05
                sl_price = round((last_price + sl_sd * std_dev) / 0.05) * 0.05
                order_info = market_order(instrument_token=instrument_token, order_type="MIS", quantity=quantity, trigger_price=0, transaction_type="SELL", price=0, tag="Sell_order")
                break
            time.sleep(1)
    elif bs_position > 0:
        if "Success" in order_info:
            tp_order_info = market_order(instrument_token=instrument_token, order_type="MIS", quantity=quantity, trigger_price=0, transaction_type="SELL", price=tp_price, tag="tp_Order_pos_buy")
            sl_order_info = market_order(instrument_token=instrument_token, order_type="MIS", quantity=quantity, trigger_price=sl_price, transaction_type="SELL", price=0, tag="sl_Order_pos_buy")

            while True:
                last_price = float(client.quote(instrument_token, quote_type='LTP')['success'][0]['lastPrice'])
                if last_price <= sl_price:
                    cancel_order_info = client.cancel_order(order_id=str(tp_order_info['Success'][exchange]['orderId']))
                    break
                elif last_price >= tp_price:
                    cancel_order_info = client.cancel_order(order_id=str(sl_order_info['Success'][exchange]['orderId']))
                    break
                else:
                    pass
                time.sleep(3)
        else:
            print("Faluire to place tp_order")

    elif bs_position < 0:
        if "Success" in order_info:
            tp_order_info = market_order(instrument_token=instrument_token, order_type="MIS", quantity=quantity, trigger_price=0, transaction_type="BUY", price=tp_price, tag="tp_Order_pos_sell")
            sl_order_info = market_order(instrument_token=instrument_token, order_type="MIS", quantity=quantity, trigger_price=sl_price, transaction_type="BUY", price=0, tag="sl_Order_pos_sell")
            while True:
                last_price = float(client.quote(instrument_token, quote_type='LTP')['success'][0]['lastPrice'])
                if last_price >= sl_price:
                    cancel_order_info = client.cancel_order(order_id=str(tp_order_info['Success'][exchange]['orderId']))
                    break
                elif last_price <= tp_price:
                    cancel_order_info = client.cancel_order(order_id=str(sl_order_info['Success'][exchange]['orderId']))
                    break
                else:
                    pass
                time.sleep(3)
        else:
            print("Faluire to place tp_order")









