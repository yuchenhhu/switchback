import cython
# from cython.cimports.libc.math import sin
from libc.math cimport sin, cos, asin, sqrt, pi


cpdef float fast_haversine(lat1: cython.float,
                          lng1: cython.float,
                          lat2: cython.float,
                          lng2: cython.float):
    """
    Calculate the great circle distance in km between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.
    """
    lng1 = lng1 * pi / 180
    lat1 = lat1 * pi / 180
    lng2 = lng2 * pi / 180
    lat2 = lat2 * pi / 180
    dlng: float = lng2 - lng1
    dlat: float = lat2 - lat1
    a: float = sin(dlat / 2.0) ** 2 + \
        cos(lat1) * cos(lat2) * sin(dlng / 2.0) ** 2
    return 6367 * 2 * asin(sqrt(a))
