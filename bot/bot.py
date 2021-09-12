import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *
import time
import math

SOCKET="wss://stream.binance.com:9443/ws/hbarbusd@kline_1m"

RSI_PERIOD = 10
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 28

# RSI_PERIOD = 2 #10
# RSI_OVERBOUGHT = 95# 65
# RSI_OVERSOLD = 90# 28
# RSI_PERIOD = 2 #10
# RSI_OVERBOUGHT = 40# 65
# RSI_OVERSOLD = 39# 28

TRADE_SYMBOL = 'HBARBUSD'
TRADE_QUANTITY = 40
LOT_STEP = 0

MAX_PROFIT_FACTOR = 1.0 / 700.0
MIN_PROFIT_FACTOR = 1.0 / 2500.0
OLD_PROFIT_FACTOR = -MAX_PROFIT_FACTOR
REALLY_OLD_PROFIT_FACTOR = -4.0 * MAX_PROFIT_FACTOR

MAX_BUY_AGE = 100
REALLY_OLD_BUY_AGE = 300
MAX_BUYS = 55
MIN_SECONDS_BETWEEN_BUYS = 15


prices = []
list_of_buys = []
list_of_buys_str = []
trade_results = []
sum_of_profits = 0
sum_of_old_age_profits = 0
last_order_time = time.time()


client = Client(config.API_KEY, config.API_SECRET)


##############
#### Utils
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


def get_profit_factor_by_age(age):
    age_inv = MAX_BUY_AGE - age
    y_shifted = age_inv * (MAX_PROFIT_FACTOR - MIN_PROFIT_FACTOR) / MAX_BUY_AGE
    return y_shifted + MIN_PROFIT_FACTOR


##############
#### Setup
trade_fee = client.get_trade_fee(symbol=TRADE_SYMBOL)
MAKER_COMMISION = float(trade_fee[0]['makerCommission'])
TAKER_COMMISION = float(trade_fee[0]['takerCommission'])
TOTAL_COMMISION = MAKER_COMMISION + TAKER_COMMISION
TRADE_QUANTITY_SELL = truncate((1 - TOTAL_COMMISION) * TRADE_QUANTITY, LOT_STEP)


##############
#### Functions
def minute_from_last_order(now1):
    global last_order_time
    if now1 - last_order_time > MIN_SECONDS_BETWEEN_BUYS:
        last_order_time = now1
        return True
    else:
        return False


def get_last_price(symbol):
    symbol_ticker = client.get_symbol_ticker(symbol=symbol)
    return float(symbol_ticker['price'])


def get_highest_bid_price(symbol):
    order_book = client.get_order_book(symbol=symbol, limit=2)
    return float(order_book['bids'][0][0])


def get_highest_bid_quantity(symbol):
    order_book = client.get_order_book(symbol=symbol, limit=2)
    return float(order_book['bids'][0][1])


def get_lowest_ask_price(symbol):
    order_book = client.get_order_book(symbol=symbol, limit=2)
    return float(order_book['asks'][0][0])


def get_lowest_ask_quantity(symbol):
    order_book = client.get_order_book(symbol=symbol, limit=2)
    return float(order_book['asks'][0][1])


def get_number_of_buys_in_queue():
    global list_of_buys
    return len(list_of_buys)


def write_lines_to_file(filename, lines):
    f = open(filename,"w")
    f.writelines(lines)
    f.close()


def update_str_list():
    global list_of_buys, list_of_buys_str
    list_of_buys_str.clear()
    for buy in list_of_buys:
        list_of_buys_str += [str(buy[0]) + ", " + str(buy[1]) + "\n"]


def add_to_list(price):
    global list_of_buys, list_of_buys_str
    list_of_buys += [[price, 0]]
    list_of_buys = sorted(list_of_buys, key=lambda x: x[0], reverse=True)
    update_str_list()
    write_lines_to_file("buy_prices.txt", list_of_buys_str)


def update_lists_after_succesful_sell(bought_price, netto_sold_price):
    global list_of_buys_str, trade_results, sum_of_profits, sum_of_old_age_profits
    profit = (netto_sold_price - bought_price[0]) * TRADE_QUANTITY_SELL
    trade_results += ["Bought price: {:.4f}, NettoSold price: {:.4f}, age: {} ---> profit: {:.5f}\n".format(bought_price[0], netto_sold_price, bought_price[1], profit)]
    sum_of_profits += profit
    sum_of_old_age_profits += profit if bought_price[1] > MAX_BUY_AGE else 0
    if len(trade_results) % 8 == 0:
        trade_results += ["Profit until now: {}\n".format(sum_of_profits)]
        trade_results += ["Income until now: {}\n".format(sum_of_profits - sum_of_old_age_profits)]
        trade_results += ["Old buy profit until now: {}\n\n".format(sum_of_old_age_profits)]
    write_lines_to_file("buy_prices.txt", list_of_buys_str)
    write_lines_to_file("trade_results.txt", trade_results)


def get_netto_price(price):
    return (1 - TOTAL_COMMISION) * price


def get_expected_netto_sell_price(symbol, side=None):

    # price = None
    # if side == SIDE_SELL:
    #     price = get_lowest_ask_price(TRADE_SYMBOL)
    # elif side == SIDE_BUY:
    #     price = get_highest_bid_price(TRADE_SYMBOL)
    # else:
    #     price = get_last_price(TRADE_SYMBOL)
    
    
    ## change this to more precise calculation (look at the quantity of highest bid an so on...)
    price = get_highest_bid_price(TRADE_SYMBOL)
    netto_price = get_netto_price(price)

    return netto_price


def profitable_price_to_sell(symbol, side):
    global list_of_buys
    expected_netto_sell_price = get_expected_netto_sell_price(symbol, side)
    for buy in list_of_buys:
        profit_factor = get_profit_factor_by_age(buy[1])
        if buy[1] > MAX_BUY_AGE:
            profit_factor = OLD_PROFIT_FACTOR
        if buy[1] > REALLY_OLD_BUY_AGE:
            profit_factor = REALLY_OLD_PROFIT_FACTOR
        
        expected_profit = expected_netto_sell_price - buy[0]
        if expected_profit >= profit_factor * buy[0]:
            return buy, expected_netto_sell_price

    return None, expected_netto_sell_price


def get_oldest_buy_older_than(max_buy_age):
    global list_of_buys
    oldest_buy = max(list_of_buys, key=lambda x: x[1])

    if oldest_buy[1] > max_buy_age:
        return oldest_buy

    return None


def update_buy_age_in_minutes():
    global list_of_buys
    for buy in list_of_buys:
        buy[1] += 1


def order(side, symbol, order_type=ORDER_TYPE_MARKET):
    price = None
    try:
        if side == SIDE_BUY:
            order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=TRADE_QUANTITY)
        elif side == SIDE_SELL:
            order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=TRADE_QUANTITY_SELL)
        fills = order['fills']
        price = float(fills[0]['price'])
        print(order)
    except Exception as e:
        print("An exception occured - {}  :(".format(e))
        return False, price

    return True, price


def on_open(ws):
    print("Opened connection!\n")


def on_close(ws):
    print("Closed connection!\n")


def on_message(ws, message):
    global prices, list_of_buys
    
    json_message = json.loads(message)
    candle = json_message['k']
    last_price = float(candle['c'])

    prices.append(last_price)
    print("\nPrice: {}".format(last_price))

    if len(prices) > RSI_PERIOD:
        np_prices = numpy.array(prices)
        rsi_list = talib.RSI(np_prices, RSI_PERIOD)
        rsi = rsi_list[-1]
        print("RSI: {}".format(rsi))

        # if get_number_of_buys_in_queue() > 0:
        #     rsi = 100

        if rsi > RSI_OVERBOUGHT:
            if get_number_of_buys_in_queue() > 0:
                profitable_bought_price, netto_price = profitable_price_to_sell(TRADE_SYMBOL, SIDE_SELL)

                if profitable_bought_price is not None:
                    print("Overbought! Sell! Sell! Sell!")
                    order_succeeded, sold_price = order(SIDE_SELL, TRADE_SYMBOL)
                    if order_succeeded:
                        list_of_buys.remove(profitable_bought_price)
                        netto_sold_price = get_netto_price(sold_price)
                        update_lists_after_succesful_sell(profitable_bought_price, netto_sold_price)
                        print("Expected NettoSold price: {}".format(netto_price))
                        print("Success!! Bought: {:.4f}, NettoSold: {:.4f} ---> profit: {:.3f}\n".format(profitable_bought_price[0], netto_sold_price, (netto_sold_price - profitable_bought_price[0]) * TRADE_QUANTITY_SELL))
                else:
                    print("It is overbought, but it is not profitable for us :(")

                # oldest_buy = get_oldest_buy_older_than(MAX_BUY_AGE)
                # if oldest_buy is not None:
                #     print("Need to sell old buy... Sell :(")
                #     order_succeeded, sold_price = order(SIDE_SELL, TRADE_SYMBOL)
                #     if order_succeeded:
                #         list_of_buys.remove(oldest_buy)
                #         netto_sold_price = get_netto_price(sold_price)
                #         update_lists_after_succesful_sell(oldest_buy, netto_sold_price)
                #         print("We made an old trade :S, Bought: {:.4f}, NettoSold: {:.4f} ---> profit: {:.3f}\n".format(oldest_buy[0], netto_sold_price, (netto_sold_price - oldest_buy[0]) * TRADE_QUANTITY_SELL))

            else:
                print("It is overbought, but we don't own any. Nothing to do.")
            
        if rsi < RSI_OVERSOLD and minute_from_last_order(time.time()):
            if get_number_of_buys_in_queue() < MAX_BUYS:
                print("Oversold! Buy! Buy! Buy!")
                order_succeeded, bought_price = order(SIDE_BUY, TRADE_SYMBOL)
                if order_succeeded:
                    add_to_list(bought_price)
            else:
                print("It is oversold, but you already own enough of it, nothing to do.")

    if candle['x']:
        update_buy_age_in_minutes()



##############
#### Main

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()

trade_results += ['Profit at the end: {}\n'.format(sum_of_profits)]
trade_results += ['Income at the end: {}\n'.format(sum_of_profits - sum_of_old_age_profits)]
trade_results += ['Old buy profit at the end: {}\n'.format(sum_of_old_age_profits)]
write_lines_to_file("trade_results.txt", trade_results)