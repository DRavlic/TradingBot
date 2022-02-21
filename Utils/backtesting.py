profit_backtesting = 2
last_buy = ...

def buy_backtesting(candlestick):
    """
    Simulate buying in backtesting, write buy order price to Candlestick object

    :param candlestick: Candlestick representation
    :type candlestick: Candlestick object
    """
    global last_buy

    price_bought = (candlestick.get_high() + candlestick.get_low()) / 2.0

    print("\n++++++++++++++++++++++++++++++++++++++++")
    print("Bought at: " + str(candlestick.get_open_time()))
    print("True price: " + str(price_bought))
    print()

    candlestick.buy_order_price = price_bought
    last_buy = price_bought


def sell_backtesting(candlestick):
    """
    Simulate selling in backtesting, write sell order price to Candlestick object

    :param candlestick: Candlestick representation
    :type candlestick: Candlestick object

    :return: Profit from last buy and sell
    """
    global last_buy

    price_sold = (candlestick.get_high() + candlestick.get_low()) / 2.0

    print("\n++++++++++++++++++++++++++++++++++++++++")
    print("Sold at: " + str(candlestick.get_open_time()))
    print("True price: " + str(price_sold))
    print()

    candlestick.sell_order_price = price_sold
    profit = price_sold - last_buy
    last_buy = ...

    return profit