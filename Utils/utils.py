import math

def truncate(number, precision):
    """ Get float number with wanted number of numbers after decimal point without rounding it

    :param number: Number to truncate (to remove some part of the decimal part of the number)
    :type number: float
    :param precision: Number of numbers to save after decimal point
    :type precision: float

    :return: float number with desired decimal places
    """
    return math.floor(number * 10 ** precision) / 10 ** precision