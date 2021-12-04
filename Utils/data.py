from enum import IntEnum
# from binance.client import Client
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

###################
#### CONSTANTS ####
###################
HOUR_IN_MS = 60*60*1000
UTC_TO_CET_OFFSET = 1
INVALID_CANDLESTICK_VALUE = -1



###################
##### CLASSES #####
###################
class HistKline(IntEnum):
    OPEN_TIME = 0
    OPEN = 1
    HIGH = 2
    LOW = 3
    CLOSE = 4
    VOLUME = 5
    CLOSE_TIME = 6

class Candlestick():
    open_time = INVALID_CANDLESTICK_VALUE
    open = INVALID_CANDLESTICK_VALUE
    high = INVALID_CANDLESTICK_VALUE
    low = INVALID_CANDLESTICK_VALUE
    close = INVALID_CANDLESTICK_VALUE
    volume = INVALID_CANDLESTICK_VALUE
    close_time = INVALID_CANDLESTICK_VALUE
    buy_order_price = INVALID_CANDLESTICK_VALUE
    sell_order_price = INVALID_CANDLESTICK_VALUE



###################
#### FUNCTIONS ####
###################
def get_historical_binance_klines(client, symbol, interval, days, utc_offset=UTC_TO_CET_OFFSET):
    """Get historical Binance Klines for desired symbol in recent days

    :param client: client with Binance private and public API keys
    :type client: Client from Binance API
    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Binance Kline interval eg. minute, hour, day etc.
    :type interval: str
    :param days: number of recent days with historical data
    :type days: int
    :param utc_offset: desired offset from UTC timezone
    :type utc_offset: int

    :return: List of klines where every kline contains the following example data:
    [
        1499040000000,      // Open time
        "0.01634790",       // Open
        "0.80000000",       // High
        "0.01575800",       // Low
        "0.01577100",       // Close
        "148976.11427815",  // Volume
        1499644799999,      // Close time
        "2434.19055334",    // Quote asset volume
        308,                // Number of trades
        "1756.87402397",    // Taker buy base asset volume
        "28.46694368",      // Taker buy quote asset volume
        "17928899.62484339" // Ignore.
    ]   
    """

    return client.get_historical_klines(symbol, interval, "{} days ago UTC+{}".format(days, utc_offset))


def get_candlesticks_from_binance_klines(klines):
    """ Get list of Candlestick objects from Binance Klines
    
    :param klines: special Binance representation of candlesticks obtained from get_historical_klines API function
    :type klines: Binance klines - presented in get_historical_binance_klines function

    :return: list of Candlestick objects
    """

    candlesticks = []
    for kline in klines:
        candlestick = Candlestick()
        candlestick.open   = float(kline[HistKline.OPEN  ])
        candlestick.high   = float(kline[HistKline.HIGH  ])
        candlestick.low    = float(kline[HistKline.LOW   ])
        candlestick.close  = float(kline[HistKline.CLOSE ])
        candlestick.volume = float(kline[HistKline.VOLUME])
        candlestick.open_time  = kline[HistKline.OPEN_TIME ]
        candlestick.close_time = kline[HistKline.CLOSE_TIME]

        candlesticks += [candlestick]

    return candlesticks


def visualize_trade(candlesticks, utc_offset=UTC_TO_CET_OFFSET):
    """Get candlesticks figure from list of Candlestick object with buy/sell orders visualization if they exist

    :param candlesticks: list of CandleStick objects
    :type candlesticks: Python list
    :param utc_offset: desired offset from UTC timezone
    :type utc_offset: int
    """

    open_time = []
    open = []
    high = []
    low = []
    close = []
    buy_orders = []
    buy_orders_str = []
    sell_orders = []
    sell_orders_str = []

    for candlestick in candlesticks:
        open += [candlestick.open]
        high += [candlestick.high]
        low += [candlestick.low]
        close += [candlestick.close]
        open_time += [pd.to_datetime(candlestick.open_time + utc_offset * HOUR_IN_MS, unit='ms')]
        
        if candlestick.buy_order_price != INVALID_CANDLESTICK_VALUE:
            buy_orders += [candlestick.buy_order_price]
            buy_orders_str += ["Buy at: {:.5f}".format(candlestick.buy_order_price)]
        else:
            buy_orders += [None]
            buy_orders_str += [None]
        
        if candlestick.sell_order_price != INVALID_CANDLESTICK_VALUE:
            sell_orders += [candlestick.sell_order_price]
            sell_orders_str += ["Sell at: {:.5f}".format(candlestick.sell_order_price)]
        else:
            sell_orders += [None]
            sell_orders_str += [None]


    candlesticks_fig = go.Candlestick(x=pd.Series(open_time),
                       open=pd.Series(open),
                       high=pd.Series(high),
                       low=pd.Series(low),
                       close=pd.Series(close),
                       showlegend=False,
                       hoverlabel = dict(namelength=0))
    
    buy_orders_fig = go.Scatter(x=open_time,
                     y=buy_orders,
                     mode="markers",
                     hoverinfo="text",
                     hovertext=buy_orders_str,
                     showlegend=False,
                     marker_symbol="x",
                     marker_color = "green",
                     marker_size = 15
                    )
    sell_orders_fig = go.Scatter(x=open_time,
                     y=sell_orders,
                     mode="markers",
                     hoverinfo="text",
                     hovertext=sell_orders_str,
                     showlegend=False,
                     marker_symbol="x",
                     marker_color = "red",
                     marker_size = 15
                    )

    figure = make_subplots()
    figure.add_trace(candlesticks_fig)
    figure.add_trace(buy_orders_fig)
    figure.add_trace(sell_orders_fig)

    figure.show()