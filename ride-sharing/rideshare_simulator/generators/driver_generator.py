import numpy as np
from typing import List

from ..driver import Driver
from ..events import DriverOnlineEvent
from ..state import WorldState
from ..utils import interpolate_latlng
from .generic import UniformBoxGenerator


class DriverOnlineGenerator(object):
    def generate(self, state: WorldState) -> List[DriverOnlineEvent]:
        raise NotImplementedError()


class UniformDriverOnlineGenerator(UniformBoxGenerator):
    def __init__(self, mean_time, min_latlng, max_latlng,
                 mean_shift_length=float("Inf"), capacity=2):
        """
            Generate a random driver in the box specified by min_latlng (left-bottom) and max_latlang (upper-right).
            The generation time of the driver follows exponential distribution with mean "mean_time". 
            The time of staying in the system for the driver follows exponential distribution with mean "mean_shift_length".
            The capacity of the driver is "capacity".
        """
        super(UniformDriverOnlineGenerator, self).__init__(
            mean_time, min_latlng, max_latlng) ## this is equivalent to super().__init__(rate, min_latlng, max_latlng)
        self.mean_shift_length = mean_shift_length
        self.capacity = capacity

    def generate(self, state: WorldState) -> List[DriverOnlineEvent]:
        """
            Generate a driver with random id and uniformly random coordinate in the box
            Return an DriverEvent with (occuring_time, driver, staying_time)
        """
        ts = state.ts + np.random.exponential(self.mean_time)
        shift_length = np.random.exponential(self.mean_shift_length)
        driver = Driver(latlng=self.get_random_latlng(), ## generate a random point
                        capacity=self.capacity)
        return [DriverOnlineEvent(ts, driver, shift_length)]
