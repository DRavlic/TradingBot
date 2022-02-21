STREAM_LINK = "wss://stream.binance.com:9443/ws/"

ALLOWED_MINUTE_INTERVALS = [1, 3, 5, 15, 30]
ALLOWED_HOUR_INTERVALS   = [1, 2, 4, 6, 8, 12]
ALLOWED_DAY_INTERVALS    = [1, 3]
ALLOWED_WEEK_INTERVALS   = [1]
ALLOWED_MONTH_INTERVALS  = [1]


def get_minute_stream(symbol, interval):
    """
    Get Binance stream with desired minute interval of candlesticks

    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Desired candlestick minute interval
    :type interval: int values [1, 3, 5, 15, 30]
    """

    if interval not in ALLOWED_MINUTE_INTERVALS:
        raise BaseException("Wrong minute interval. Check inputs of get_minute_stream function!")

    return STREAM_LINK + symbol.lower() + "@kline_{}m".format(interval)


def get_hour_stream(symbol, interval):
    """
    Get Binance stream with desired hour interval of candlesticks

    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Desired candlestick hour interval
    :type interval: int values [1, 2, 4, 6, 8, 12]
    """

    if interval not in ALLOWED_HOUR_INTERVALS:
        raise BaseException("Wrong hour interval. Check inputs of get_hour_stream function!")

    return STREAM_LINK + symbol.lower() + "@kline_{}h".format(interval)


def get_day_stream(symbol, interval):
    """
    Get Binance stream with desired day interval of candlesticks

    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Desired candlestick day interval
    :type interval: int values [1, 3]
    """

    if interval not in ALLOWED_DAY_INTERVALS:
        raise BaseException("Wrong day interval. Check inputs of get_day_stream function!")

    return STREAM_LINK + symbol.lower() + "@kline_{}d".format(interval)


def get_week_stream(symbol, interval):
    """
    Get Binance stream with desired week interval of candlesticks

    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Desired candlestick week interval
    :type interval: int values [1]
    """

    if interval not in ALLOWED_WEEK_INTERVALS:
        raise BaseException("Wrong week interval. Check inputs of get_week_stream function!")

    return STREAM_LINK + symbol.lower() + "@kline_{}w".format(interval)


def get_month_stream(symbol, interval):
    """
    Get Binance stream with desired month interval of candlesticks

    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Desired candlestick month interval
    :type interval: int values [1]
    """

    if interval not in ALLOWED_MONTH_INTERVALS:
        raise BaseException("Wrong month interval. Check inputs of get_month_stream function!")

    return STREAM_LINK + symbol.lower() + "@kline_{}M".format(interval)


def on_open(ws):
    """
    Do when Binance connection is opened

    :param ws: websocket
    :type ws: Binance WebSocketApp
    """

    print("Opened connection!\n")


def on_close(ws):
    """
    Do when Binance connection is closed

    :param ws: websocket
    :type ws: Binance WebSocketApp
    """

    print("Closed connection!\n")
