from binance.client import Client
from binance.enums import *
from decimal import Decimal
import json
import math
import numpy as np
import pandas as pd
import sys
import talib

# import time
from time import localtime, sleep, strftime, time

import websocket


####################
### Parameters
SYMBOL = "ONEBUSD"
TRADE_QUANTITY_BUSD = 200

ADJUSTED_FACTOR_REAL_PRICE = 1.7
ADJUSTED_FACTOR_PRICE_PREDICTION = 0.3
MAX_LIST_SIZE = 20
LIST_LENGTH_FOR_PRICE_PREDICTION = 6
LARGE_EMA_WINDOW = 18 # 6
SMALL_EMA_WINDOW = 6 # 3
MIN_MINUTES_FOR_BUYING = 6
MIN_MINUTES_FOR_SELLING = 3
MIN_EMA_DIFFERENCE_FACTOR = 0.0005
FAKE_BUY_SIGNAL_FACTOR = 0.0065

INITIAL_VALUE = -1

last_trade = time()

# Enter the buying or selling opportunity when we are sure the last LIST_LENGTH_FOR_PRICE_PREDICTION
# is calculated on adjusted prices. Code is implemented to start filling adjusted prices with real
# closed prices for the first LIST_LENGTH_FOR_PRICE_PREDICTION minutes and after that it starts to
# fill adjusted prices the way they are supposed to be calculated (because from that moment we can 
# calculate price prediction). But if we look closely, we need to wait additional 
# LIST_LENGTH_FOR_PRICE_PREDICTION minutes to work with all the prices that were adjusted.
# Because of that, we need to make sure condition that is written below this comment. Otherwise, 
# we'll never enter buying or selling opportunity.
if 2 * LIST_LENGTH_FOR_PRICE_PREDICTION > MAX_LIST_SIZE:
    raise BaseException("List length for price prediction is too big!")
if ADJUSTED_FACTOR_REAL_PRICE + ADJUSTED_FACTOR_PRICE_PREDICTION != 2.0:
    raise BaseException("Two factor for adjusted price needs to sum up to 2.0!")


####################
### Import Binance API private and public key
# sys.path.append('../')
import config
client = Client(config.API_KEY, config.API_SECRET)


####################
### Setup
stream = "wss://stream.binance.com:9443/ws/" + SYMBOL.lower() + "@kline_1m"
trade_fee = client.get_trade_fee(symbol=SYMBOL)
taker_commission = float(trade_fee[0]['takerCommission'])
waiting_for_buying_opportunity = True

real_closed_prices = [INITIAL_VALUE]
adjusted_prices = [INITIAL_VALUE]
large_ema_values = [INITIAL_VALUE]
small_ema_values = [INITIAL_VALUE]
price_prediction = INITIAL_VALUE
coins_bought = INITIAL_VALUE
price_bought = INITIAL_VALUE
profit = 0

step_size = INITIAL_VALUE
for filter in client.get_symbol_info(SYMBOL)['filters']:
    if filter['filterType'] == 'LOT_SIZE':
        step_size_str = filter['stepSize'].replace('.', '')
        step_size = step_size_str.find('1')


####################
### Utils
def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor



####################
### Functions
def get_last_price(symbol):
    symbol_ticker = client.get_symbol_ticker(symbol=symbol)
    return float(symbol_ticker['price'])


def get_highest_bid_price(symbol):
    order_book = client.get_order_book(symbol=symbol, limit=2)
    return float(order_book['bids'][0][0])


def get_coin_trade_quantity(trade_quantity_busd):
    global step_size

    coins_available = trade_quantity_busd / get_last_price(SYMBOL)
    return truncate(coins_available, step_size)


def buy(order_type=ORDER_TYPE_MARKET):
    global coins_bought, price_bought, real_closed_prices, adjusted_prices, price_prediction, small_ema_values, large_ema_values
    global waiting_for_buying_opportunity, taker_commission
    global last_trade

    coin_trade_quantity = get_coin_trade_quantity(TRADE_QUANTITY_BUSD)
    try:
        order = client.create_order(symbol=SYMBOL, side=SIDE_BUY, type=order_type, quantity=coin_trade_quantity)
        
        last_trade = time()
        waiting_for_buying_opportunity = False

        fills = order['fills']
        price = 0
        quantity = 0
        commission = 0
        for i in range(0, len(fills)):
            price += float(fills[i]['qty']) * float(fills[i]['price'])
            quantity += float(fills[i]['qty'])
            commission += float(fills[i]['commission'])
        price = price / quantity

        coins_bought = quantity - commission
        price_bought = (price * quantity) / coins_bought # total money spent over total number of coins in the end

        print("\n++++++++++++++++++++++++++++++++++++++++")
        print("Bought at: " + str(strftime("%Y-%m-%d %H:%M:%S", localtime())))
        print("At price: " + str(price) + " and True price: " + str(price_bought))
        print("++++++++++++++++++++++++++++++++++++++++\n")
        
    except Exception as e:
        print("An exception occured while buying - {}".format(e))


def sell(order_type=ORDER_TYPE_MARKET):
    global coins_bought, price_bought, step_size, profit, real_closed_prices, adjusted_prices, price_prediction, small_ema_values, large_ema_values
    global waiting_for_buying_opportunity, taker_commission
    global last_trade

    coin_trade_quantity = truncate(coins_bought, step_size)
    try:
        order = client.create_order(symbol=SYMBOL, side=SIDE_SELL, type=order_type, quantity=coin_trade_quantity)
        
        last_trade = time()
        waiting_for_buying_opportunity = True

        fills = order['fills']
        price = 0
        quantity = 0
        commission = 0
        for i in range(0, len(fills)):
            price += float(fills[i]['qty']) * float(fills[i]['price'])
            quantity += float(fills[i]['qty'])
            commission += float(fills[i]['commission'])
        price = price / quantity

        price_sell = price - (commission / quantity) # sold price minus commission for every coin that was sold
        profit += (price * quantity - commission) - (price_bought * coins_bought)

        print("\n++++++++++++++++++++++++++++++++++++++++")
        print("Sold at: " + str(strftime("%Y-%m-%d %H:%M:%S", localtime())))
        print("At price: " + str(price) + " and True price: " + str(price_sell))
        print("Price difference: " + str(price_sell - price_bought))
        print("Trade profit: " + str((price * quantity - commission) - (price_bought * coins_bought)))
        print("Current profit: " + str(profit))
        print("++++++++++++++++++++++++++++++++++++++++\n")
        
    except Exception as e:
        print("An exception occured while selling - {}".format(e))


def get_ema(prices, window):
    prices_for_calculation = prices[-window:]
    ema_pandas = talib.EMA(pd.Series(prices_for_calculation), window)
    ema_value = ema_pandas[ema_pandas.size - 1]

    return ema_value


def get_new_price_prediction(prices):
    if len(prices) == 0:
        raise BaseException("There must be at least one price for price prediction!")
    elif len(prices) == 1:
        return prices[-1]
    else:
        x = np.arange(0, len(prices))
        y = np.array(prices)
        a, b = np.polyfit(x, y, 1)

        return a * len(prices) + b


def get_adjusted_price(real_price, price_prediction):
    return (ADJUSTED_FACTOR_REAL_PRICE * real_price + ADJUSTED_FACTOR_PRICE_PREDICTION * price_prediction) / 2.0


def update_data(candle):
    global real_closed_prices, adjusted_prices, price_prediction, small_ema_values, large_ema_values

    last_price = float(candle["c"])
    real_closed_prices[-1] = last_price
    
    if price_prediction != INITIAL_VALUE:
        adjusted_prices[-1] = get_adjusted_price(last_price, price_prediction)
    else:
        adjusted_prices[-1] = last_price

    if len(real_closed_prices) >= LARGE_EMA_WINDOW:
        small_ema_values[-1] = get_ema(real_closed_prices, SMALL_EMA_WINDOW)
        large_ema_values[-1] = get_ema(real_closed_prices, LARGE_EMA_WINDOW)


def minutes_small_ema_is_under_large_ema():
    global small_ema_values, large_ema_values
    
    minutes_under = 0
    # don't look at last ema values
    for i in range(1, len(small_ema_values)):
        if small_ema_values[-i-1] <= large_ema_values[-i-1]:
            minutes_under += 1
        elif i == 1 and (small_ema_values[-i-1] - large_ema_values[-i-1]) <= (MIN_EMA_DIFFERENCE_FACTOR * small_ema_values[-i-1]):
            minutes_under += 1
        else:
            break

    return minutes_under


def minutes_small_ema_is_over_large_ema():
    global small_ema_values, large_ema_values
    
    minutes_over = 0
    # don't look at last ema values
    for i in range(1, len(small_ema_values)): # razlog zasto bi trebali u isto vrijeme puniti i small i large ema values - ili promijeniti ovaj uvjet
        if small_ema_values[-i-1] >= large_ema_values[-i-1]:
            minutes_over += 1
        elif i == 1 and (large_ema_values[-i-1] - small_ema_values[-i-1]) <= (MIN_EMA_DIFFERENCE_FACTOR * large_ema_values[-i-1]):
            minutes_over += 1
        else:
            break

    return minutes_over


def is_small_ema_over_large_ema():
    global small_ema_values, large_ema_values

    ema_diff = small_ema_values[-1] - large_ema_values[-1]
    return ema_diff > MIN_EMA_DIFFERENCE_FACTOR * small_ema_values[-1]


def is_small_ema_under_large_ema():
    global small_ema_values, large_ema_values

    ema_diff = large_ema_values[-1] - small_ema_values[-1]
    return ema_diff > MIN_EMA_DIFFERENCE_FACTOR * large_ema_values[-1]


def was_fake_buy_signal():
    global price_bought
    
    highest_bid_price = get_highest_bid_price(SYMBOL)
    return price_bought - highest_bid_price > FAKE_BUY_SIGNAL_FACTOR * price_bought


def buy_if_possible():
    global adjusted_prices, waiting_for_buying_opportunity
    global last_trade

    if len(adjusted_prices) >= 2 * LIST_LENGTH_FOR_PRICE_PREDICTION: # change this to something more clear
        if minutes_small_ema_is_under_large_ema() >= MIN_MINUTES_FOR_BUYING and is_small_ema_over_large_ema():
            buy()

    # if time() - last_trade > 5:
    #     buy()


def sell_if_possible():
    global adjusted_prices, waiting_for_buying_opportunity
    global last_trade

    if len(adjusted_prices) >= 2 * LIST_LENGTH_FOR_PRICE_PREDICTION: # change this to something more clear, this is not necessary here I think?
        # if (minutes_small_ema_is_over_large_ema() >= MIN_MINUTES_FOR_SELLING and is_small_ema_under_large_ema()) or was_fake_buy_signal():
        # if is_small_ema_under_large_ema():
        if (time() - last_trade >= 60 * MIN_MINUTES_FOR_SELLING and is_small_ema_under_large_ema()) or was_fake_buy_signal():
            sell()

    # if time() - last_trade > 5:
    #     sell()


def create_new_minute():
    global real_closed_prices, adjusted_prices, price_prediction, small_ema_values, large_ema_values

    print("##############################################")
    print("Real_closed_prices:")
    for i in range(0, min(LIST_LENGTH_FOR_PRICE_PREDICTION, len(real_closed_prices))):
        print("{:.4f}".format(real_closed_prices[-i-1]), end=" ")
    print()
    # print("Adjusted_prices:")
    # for i in range(0, min(LIST_LENGTH_FOR_PRICE_PREDICTION, len(adjusted_prices))):
    #     print("{:.4f}".format(adjusted_prices[-i-1]), end=" ")
    # print()
    print("Small_ema_values:")
    for i in range( 0, min(LIST_LENGTH_FOR_PRICE_PREDICTION, len(small_ema_values))):
        print("{:.4f}".format(small_ema_values[-i-1]), end=" ")
    print()
    print("Large_ema_values:")
    for i in range(0, min(LIST_LENGTH_FOR_PRICE_PREDICTION, len(large_ema_values))):
        print("{:.4f}".format(large_ema_values[-i-1]), end=" ")
    print("\n##############################################")

    if len(adjusted_prices) >= LIST_LENGTH_FOR_PRICE_PREDICTION:
        price_prediction = get_new_price_prediction(adjusted_prices[-LIST_LENGTH_FOR_PRICE_PREDICTION:])

    if len(adjusted_prices) >= LARGE_EMA_WINDOW:
        large_ema_values += [INITIAL_VALUE]
        small_ema_values += [INITIAL_VALUE]
    real_closed_prices += [INITIAL_VALUE]
    adjusted_prices += [INITIAL_VALUE]

    # trim old data
    if len(real_closed_prices) > MAX_LIST_SIZE:
        real_closed_prices.pop(0)
    if len(adjusted_prices) > MAX_LIST_SIZE:
        adjusted_prices.pop(0)
    if len(large_ema_values) > MAX_LIST_SIZE:
        large_ema_values.pop(0)
    if len(small_ema_values) > MAX_LIST_SIZE:
        small_ema_values.pop(0)


def on_open(ws):
    print("Opened connection!\n")


def on_close(ws):
    print("Closed connection!\n")


def on_message(ws, message):
    global waiting_for_buying_opportunity

    json_message = json.loads(message)
    candle = json_message['k']
    update_data(candle)

    if waiting_for_buying_opportunity:
        buy_if_possible()
    else:
        sell_if_possible()

    one_minute_passed = candle['x']
    # print("one_minute_passed: ", one_minute_passed)
    if one_minute_passed:
        create_new_minute()




####################
### Main
ws = websocket.WebSocketApp(stream, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever(ping_timeout=30)

print("\nProfit: " + str(profit))