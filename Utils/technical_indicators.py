from Utils.data import Candlestick
from Utils.utils import *
from tradingview_ta import TA_Handler, Interval
from math import sqrt

import numpy as np
import pandas as pd


### TO DO: provide new parameter which will tell you which value of Candlestick object to use:
### this can be done as providing function parameter with default value of Candelstick.get_close????
## if you do this, then change description of some comments because there can be mention of close price

### decide wether we will divide by n or n-1 in Standard deviation and Variance

# probaj staviti int smoohing factor ili nesto kod njega promijeniti mzoda?
# probaj pamtiti dosta ema-a i svega sto se racuna rekurzivno


def SMA(candlesticks, period, precision=4):
    """
    Calculate Simple Moving Average on close prices of Candlestick objects list
    Formula at: https://www.investopedia.com/terms/s/sma.asp

    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: SMA period
    :type period: int

    :return: Simple Moving Average value
    """

    sum = 0
    num_of_candles = len(candlesticks)

    for i in range(0, period):
        sum += candlesticks[num_of_candles - i - 1].get_close()

    return round(sum / period, precision)


def SMA_list(prices, precision=4):
    """
    Calculate Simple Moving Average on list of prices
    Formula at: https://www.investopedia.com/terms/s/sma.asp

    :param prices: List of prices
    :type prices: Python list
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Simple Moving Average value
    """

    sum = 0
    for price in prices:
        sum += price

    return round(sum / len(prices), precision)


def Var(candlesticks, period, precision=4):
    """
    Calculate Variance of candlestick close prices over given period
    Formula at: https://www.investopedia.com/terms/v/variance.asp

    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: number of last prices from candlesticks list for Variance calculation
    :type period: int
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Variance over given values
    """

    avg = SMA(candlesticks, period)
    sum = 0
    num_of_candles = len(candlesticks)

    for i in range(0, period):
        # if candlesticks[num_of_candles - i - 1].get_close() - avg <= 0.0001:
        #     sum += 15
        # else:
        #     sum += (candlesticks[num_of_candles - i - 1].get_close() - avg) ** 2
        sum += (candlesticks[num_of_candles - i - 1].get_close() - avg) ** 2

    return round(sum / num_of_candles, precision)


def Var_list(prices, precision=4):
    """
    Calculate Variance on list of prices
    Formula at: https://www.investopedia.com/terms/v/variance.asp

    :param prices: List of prices
    :type prices: Python list
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Variance over given values
    """

    avg = SMA_list(prices)
    sum = 0

    for price in prices:
        sum += (price - avg) ** 2

    return round(sum / len(prices), precision)


def Std(candlesticks, period, precision=4):
    """
    Calculate standard deviation of candlestick close prices over given period
    Formula at: https://www.investopedia.com/terms/s/standarddeviation.asp

    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: number of last prices from candlesticks list for Standard deviation calculation
    :type period: int
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Standard deviation over given values
    """

    return round(sqrt(Var(candlesticks, period)), precision)


def Std_list(prices, precision=4):
    """
    Calculate Standard deviation on list of prices
    Formula at: https://www.investopedia.com/terms/s/standarddeviation.asp

    :param prices: List of prices
    :type prices: Python list
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Standard deviation over given values
    """

    return round(sqrt(Var_list(prices)), precision)


def EMA(candlesticks, period, smoothing_factor=2, precision=4):
    """
    Calculate Exponential Moving Average on close prices of Candlestick objects list with desired period and smoothing_factor
    Formula: https://python.plainenglish.io/how-to-calculate-the-ema-of-a-stock-with-python-5d6fb3a29f5
    
    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: EMA period
    :type period: int
    :param smoothing_factor: EMA smoothing factor
    :type smoothing_factor: float
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Exponential Moving Average value
    """

    factor = smoothing_factor / (1 + period)
    num_of_candlesticks = len(candlesticks)
    if num_of_candlesticks < 2 * period:
        raise BaseException("Can't calculate EMA. Provide bigger list of Candlestick objects list!")

    sma = round(SMA(candlesticks[num_of_candlesticks - 2 * period:num_of_candlesticks - period], period), precision)
    ema = [round(candlesticks[num_of_candlesticks - period].get_close() * factor + sma * (1 - factor), precision)]

    for i in range(1, period):
        ema += [round(candlesticks[num_of_candlesticks - period + i].get_close() * factor + ema[-1] * (1 - factor), precision)]

    return round(ema[-1], precision)


def EMA_list(prices, smoothing_factor=2, precision=4):
    """
    Calculate Exponential Moving Average on list of prices with desired period and smoothing_factor.
    This function differs from EMA function by not using Simple Moving Average as starting point but
    rather it uses first element of a list for starting point of Exponential Moving Average function.
    Formula: https://python.plainenglish.io/how-to-calculate-the-ema-of-a-stock-with-python-5d6fb3a29f5
    
    :param prices: List of prices
    :type prices: Python list
    :param smoothing_factor: EMA smoothing factor
    :type smoothing_factor: float
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Exponential Moving Average value
    """

    period = len(prices)
    factor = smoothing_factor / (1 + period)

    ema = [round(prices[0], precision)]
    for i in range(1, period):
        ema += [round(prices[i] * factor + ema[-1] * (1 - factor), precision)]

    return round(ema[-1], precision)


def RSI(candlesticks, period=14, precision=4):
    """
    Calculate RSI indicator with Simple Moving Average with desired period on close prices.
    Formula at: https://www.macroption.com/rsi-calculation/

    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: RSI period
    :type period: int
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: RSI value
    """
    
    if period > len(candlesticks) + 1:
        raise BaseException("Too large RSI period for given candlesticks!")

    period_indexes = [len(candlesticks) - i - 1 for i in range(period)]
    price_changes  = [candlesticks[i].get_close() - candlesticks[i - 1].get_close() for i in period_indexes]

    up_move_changes   = [price_change      if price_change > 0 else 0 for price_change in price_changes]
    down_move_changes = [abs(price_change) if price_change < 0 else 0 for price_change in price_changes]

    if len(up_move_changes) != period or len(down_move_changes) != period:
        raise BaseException("Wrong RSI calculation. Check RSI function!")

    sma_up_move_change   = SMA_list(up_move_changes)
    sma_down_move_change = SMA_list(down_move_changes)

    if sma_down_move_change == 0:
        return 100

    rs = sma_up_move_change / sma_down_move_change

    return round(100 - 100 / (1 + rs), precision)


def RSI_ema(candlesticks, period=14, smoothing_factor=2, precision=4):
    """
    Calculate RSI indicator with Exponential Moving Average with desired smoothing factor on close prices.
    Formula at: https://www.macroption.com/rsi-calculation/

    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: RSI period
    :type period: int
    :param smoothing_factor: EMA smoothing factor
    :type smoothing_factor: float
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: RSI value
    """
    
    if period > len(candlesticks) + 1:
        raise BaseException("Too large RSI period for given candlesticks!")

    period_indexes = [len(candlesticks) - i - 1 for i in range(period)]
    price_changes  = [candlesticks[i].get_close() - candlesticks[i - 1].get_close() for i in period_indexes]

    up_move_changes   = [price_change      if price_change > 0 else 0 for price_change in price_changes]
    down_move_changes = [abs(price_change) if price_change < 0 else 0 for price_change in price_changes]

    if len(up_move_changes) != period or len(down_move_changes) != period:
        raise BaseException("Wrong RSI calculation. Check RSI_ema function!")

    ema_up_move_change   = EMA_list(up_move_changes, smoothing_factor)
    ema_down_move_change = EMA_list(down_move_changes, smoothing_factor)

    if ema_down_move_change == 0:
        return 100

    rs = ema_up_move_change / ema_down_move_change

    return round(100 - 100 / (1 + rs), precision)


def MACD(candlesticks,
         ema1_period=12,
         ema2_period=26,
         signal_line_ema_period=9,
         ema_smoothing_factor=2,
         precision=4):
    """
    Calculate MACD and its singal line value with desired values for EMA periods and smoothing factors.
    Calculation at: https://www.investopedia.com/ask/answers/122414/what-moving-average-convergence-divergence-macd-formula-and-how-it-calculated.asp

    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param ema1_period: period of first EMA value in MACD formula 
    :type ema1_period: float
    :param ema2_period: period of second EMA value in MACD formula 
    :type ema2_period: float
    :param signal_line_ema_period: period of EMA value for MACD signal line 
    :type signal_line_ema_period: float
    :param ema_smoothing_factor: snoothing factor for all EMA values
    :type ema_smoothing_factor: float
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Tuple of MACD and its signal line value
    """

    num_of_candlesticks = len(candlesticks)
    macd = []

    for i in range(num_of_candlesticks - signal_line_ema_period, num_of_candlesticks):
        ema1 = EMA(candlesticks[:i+1], ema1_period, ema_smoothing_factor)
        ema2 = EMA(candlesticks[:i+1], ema2_period, ema_smoothing_factor)
        macd += [ema1 - ema2]

    ema_signal = EMA_list(macd, ema_smoothing_factor)

    return round(macd[-1], precision), round(ema_signal, precision)


def Bollinger_bands(candlesticks, period=20, std_multiplier=2, precision=4):
    """
    Calculate Upper and Lower Bollinger bands with desired values of std_multiplier and period which tells us on how 
    many last close prices Bollinger bands should be calculated.
    Formula at: https://www.investopedia.com/terms/b/bollingerbands.asp


    :param candlesticks: List of Candlestick objects
    :type candlesticks: Python list
    :param period: number of last Candlestick objects from candlesticks list to calculate on
    :type period: int
    :param std_multiplier: Standard deviation multiplier. Default value is 2
    :type std_multiplier: int
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Tuple of Upper and Lower Bollinger bands
    """

    avg = SMA(candlesticks, period)
    std = Std(candlesticks, period)

    upper_bb = avg + std_multiplier * std
    lower_bb = avg - std_multiplier * std

    return round(upper_bb, precision), round(lower_bb, precision)



def SMA_tradingview(symbol, interval, sma_period, exchange="Binance", precision=4):
    """
    Get SMA with desired period from TradingView in real time. Past data from TradingView is not supported at this moment and 
    cannot be used for backtesting!

    :param symbol: ticker of the cryptocurrency
    :type symbol: str
    :param interval: candlestick interval
    :type interval: one of tradingview_ta.Interval types
    :param sma_period: SMA period
    :type sma_period: int, possible choices: [5, 10, 20, 30, 50, 100, 200]
    :param exchange: exchange from which data is pulled
    :type exchange: str
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: SMA with desired period from TradingView in real time
    """

    sma = -1
    try:
        crypto = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange=exchange,
            interval=interval
        )

        sma = crypto.get_analysis().indicators['SMA' + str(sma_period)]
    except:
        print("TradingView server, your internet access or your parameters is wrong. Check SMA_tradingview function!")
    
    return round(sma, precision)


def EMA_tradingview(symbol, interval, ema_period, exchange="Binance", precision=4):
    """
    Get EMA with desired period from TradingView in real time. Past data from TradingView is not supported at this moment and 
    cannot be used for backtesting!

    :param symbol: ticker of the cryptocurrency
    :type symbol: str
    :param interval: candlestick interval
    :type interval: one of tradingview_ta.Interval types
    :param ema_period: EMA period
    :type ema_period: int, possible choices: [5, 10, 20, 30, 50, 100, 200]
    :param exchange: exchange from which data is pulled
    :type exchange: str
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: EMA with desired period from TradingView in real time
    """

    ema = -1
    try:
        crypto = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange=exchange,
            interval=interval
        )

        ema = crypto.get_analysis().indicators['EMA' + str(ema_period)]
    except:
        print("TradingView server, your internet access or your parameters is wrong. Check EMA_tradingview function!")
    
    return round(ema, precision)

    
def RSI_tradingview(symbol, interval, exchange="Binance", precision=4):
    """
    Get RSI with period of 14 from TradingView in real time. Past data from TradingView is not supported at this moment and 
    cannot be used for backtesting!

    :param symbol: ticker of the cryptocurrency
    :type symbol: str
    :param interval: candlestick interval
    :type interval: one of tradingview_ta.Interval types
    :param exchange: exchange from which data is pulled
    :type exchange: str
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: RSI from TradingView in real time
    """

    rsi = -1
    try:
        crypto = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange=exchange,
            interval=interval
        )

        rsi = crypto.get_analysis().indicators['RSI']
    except:
        print("TradingView server, your internet access or your parameters is wrong. Check RSI_tradingview function!")
    
    return round(rsi, precision)


def MACD_tradingview(symbol, interval, exchange="Binance", precision=4):
    """
    Get MACD and its singal line from TradingView in real time. Past data from TradingView is not supported at this 
    moment and cannot be used for backtesting!

    :param symbol: ticker of the cryptocurrency
    :type symbol: str
    :param interval: candlestick interval
    :type interval: one of tradingview_ta.Interval types
    :param exchange: exchange from which data is pulled
    :type exchange: str
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Tuple of MACD and its signal line value from TradingView in real time
    """

    macd = -1
    macd_signal = -1
    try:
        crypto = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange=exchange,
            interval=interval
        )

        macd = crypto.get_analysis().indicators['MACD.macd']
        macd_signal = crypto.get_analysis().indicators['MACD.signal']
    except:
        print("TradingView server, your internet access or your parameters is wrong. Check MACD_tradingview function!")
    
    return round(macd, precision), round(macd_signal, precision)


def Bollinger_bands_tradingview(symbol, interval, exchange="Binance", precision=4):
    """
    Get Upper and Lower Bollinger bands from TradingView in real time. Past data from TradingView is not supported 
    at this moment and cannot be used for backtesting!

    :param symbol: ticker of the cryptocurrency
    :type symbol: str
    :param interval: candlestick interval
    :type interval: one of tradingview_ta.Interval types
    :param exchange: exchange from which data is pulled
    :type exchange: str
    :param precision: number of decimal to round a float number
    :type precision: int

    :return: Tuple of Upper and Lower Bollinger bands from TradingView in real time
    """

    upper_bb = -1
    lower_bb = -1
    try:
        crypto = TA_Handler(
            symbol=symbol,
            screener="crypto",
            exchange=exchange,
            interval=interval
        )

        upper_bb = crypto.get_analysis().indicators['BB.upper']
        lower_bb = crypto.get_analysis().indicators['BB.lower']
        # print(crypto.get_analysis().indicators)
    except:
        print("TradingView server, your internet access or your parameters is wrong. Check Bollinger_bands_tradingview function!")
    
    return round(upper_bb, precision), round(lower_bb, precision)