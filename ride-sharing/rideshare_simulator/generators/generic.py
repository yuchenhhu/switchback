from typing import Tuple
from uuid import uuid4

import numpy as np

from ..utils import interpolate_latlng


class UniformBoxGenerator(object):
    """
    Generates objects at random from a box-shaped region, with
    exponential interarrival times with mean `mean_time.`
    """
    def __init__(self, mean_time: float,
                 min_latlng: Tuple[float, float],
                 max_latlng: Tuple[float, float]):
        """
            mean_time: the mean interrarival time
            min_latlng: min latitude and min longitude (a tuple)
            max_latlng: max latitude and max longitude (a tuple)
        """
        self.mean_time = mean_time
        self.min_latlng = min_latlng
        self.max_latlng = max_latlng

    def get_random_latlng(self):
        """
            return a uniformly random point from the box specified by min_latlng and max_latlng
        """
        return interpolate_latlng(
            self.min_latlng, self.max_latlng,
            p=np.random.rand(), plng=np.random.rand())

