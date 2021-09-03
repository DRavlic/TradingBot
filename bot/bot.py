import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET="wss://stream.binance.com:9443/ws/hbarbusd@kline_1m"

RSI_PERIOD = 7
RSI_OVERBOUGHT = 70# 85
RSI_OVERSOLD = 28# 20
TRADE_SYMBOL = 'HBARBUSD'
TRADE_QUANTITY = 60
MAX_BUYS = 20
PROFIT_FACTOR = 1.0 / 100.0

prices = []
list_of_buys = []
list_of_buys_str = []
trade_results = []
sum_of_profits = 0

client = Client(config.API_KEY, config.API_SECRET)

import time

last_order_time = time.time()
def minute_from_last_order(now1):
    global last_order_time
    if now1 - last_order_time > 45:
        last_order_time = now1
        return True
    else:
        return False

##############
#### Functions
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
    for price in list_of_buys:
        list_of_buys_str += [str(price) + "\n"]


def add_to_list(price):
    global list_of_buys, list_of_buys_str
    list_of_buys += [price]
    list_of_buys.sort()
    update_str_list()
    write_lines_to_file("buy_prices.txt", list_of_buys_str)


def remove_from_list(bought_price, sold_price):
    global list_of_buys, list_of_buys_str, trade_results, sum_of_profits
    list_of_buys.remove(bought_price)
    list_of_buys_str.remove(str(bought_price) + "\n")
    profit = (sold_price - bought_price) * TRADE_QUANTITY
    trade_results += ["Bought price: {}, Sold price: {} ---> profit: {:.3f}\n".format(bought_price, sold_price, profit)]
    sum_of_profits += profit
    write_lines_to_file("buy_prices.txt", list_of_buys_str)
    write_lines_to_file("trade_results.txt", trade_results)


def get_netto_price(symbol, side=None):
    trade_fee = client.get_trade_fee(symbol=symbol)
    maker_commission = float(trade_fee[0]['makerCommission'])
    taker_commission = float(trade_fee[0]['takerCommission'])

    price = None
    if side == SIDE_SELL:
        price = get_lowest_ask_price(TRADE_SYMBOL)
    elif side == SIDE_BUY:
        price = get_highest_bid_price(TRADE_SYMBOL)
    else:
        price = get_last_price(TRADE_SYMBOL)

    return (1 - maker_commission + taker_commission) * price


def profitable_price_to_sell(symbol, side):
    global list_of_buys
    netto_price = get_netto_price(symbol, side)
    for bought_price in list_of_buys:
        if netto_price - bought_price >= PROFIT_FACTOR * netto_price:
            return bought_price, netto_price

    return None, netto_price


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        order = client.create_test_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("An exception occured - {}  :(".format(e))
        return False

    return True


def on_open(ws):
    print("Opened connection!\n")


def on_close(ws):
    print("Closed connection!\n")


def on_message(ws, message):
    global prices
    
    json_message = json.loads(message)
    candle = json_message['k']
    last_price = float(candle['c'])

    prices.append(last_price)
    print("Price: {}".format(last_price))

    if len(prices) > RSI_PERIOD:
        np_prices = numpy.array(prices)
        rsi_list = talib.RSI(np_prices, RSI_PERIOD)
        rsi = rsi_list[-1]
        # print("RSI: {}\n".format(rsi))

        # if get_number_of_buys_in_queue() > 1:
        #     rsi = 100
        #     print("Promijenio sam RSI namjerno!!")
        print("RSI: {}\n".format(rsi))

        if rsi > RSI_OVERBOUGHT:
            if get_number_of_buys_in_queue() > 0:
                last_price = get_last_price(TRADE_SYMBOL)
                profitable_bought_price, netto_price = profitable_price_to_sell(TRADE_SYMBOL, SIDE_SELL)
                if profitable_bought_price is not None:
                    print("Overbought! Sell! Sell! Sell!")
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        ## this is not precise, use order variable next time
                        remove_from_list(profitable_bought_price, netto_price)
                        print("Success!! Bought: {}, Sold: {} ---> profit: {:.3f}\n".format(profitable_bought_price, netto_price, (netto_price - profitable_bought_price) * TRADE_QUANTITY))
                else:
                    print("It is overbought, but it is not profitable for us :(")
            else:
                print("It is overbought, but we don't own any. Nothing to do.")
            
        if rsi < RSI_OVERSOLD and minute_from_last_order(time.time()):
            if get_number_of_buys_in_queue() < MAX_BUYS:
                print("Oversold! Buy! Buy! Buy!")
                order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                if order_succeeded:
                    ## this is not precise, use order variable next time
                    last_price = get_last_price(TRADE_SYMBOL)
                    add_to_list(last_price)
            else:
                print("It is oversold, but you already own enough of it, nothing to do.")



##############
#### Main

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()

trade_results += ['Profit at the end: {}'.format(sum_of_profits)]
write_lines_to_file("trade_results.txt", trade_results)