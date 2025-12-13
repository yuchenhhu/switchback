from abc import abstractmethod, ABC
import uuid
from typing import List, Tuple

import numpy as np
import pandas as pd

from ..events import RequestDispatchEvent
from ..rider import Rider
from ..state import WorldState
from .generic import UniformBoxGenerator


class RequestGenerator(ABC):
    @abstractmethod
    def generate(self, state: WorldState) -> List[RequestDispatchEvent]:
        pass


class UniformRequestGenerator(UniformBoxGenerator, RequestGenerator):
    def __init__(self, mean_time: float,
                 min_latlng: Tuple[float, float],
                 max_latlng: Tuple[float, float],
                 rider_ctor=Rider,
                 rider_params=None):
        """
        Creates riders at random using rider_ctor, which is a
        constructor of the form:

        rider_ctor(src_latlng, dest_latlng) -> Rider

        :param rider_params Additional params to be passed to the rider constructor.
        """
        super(UniformRequestGenerator, self).__init__(
            mean_time, min_latlng, max_latlng)
        self.rider_ctor = rider_ctor
        self.rider_params = dict() if rider_params is None else rider_params

    def generate(self, state: WorldState) -> List[RequestDispatchEvent]:
        ts = state.ts + np.random.exponential(self.mean_time)
        src = self.get_random_latlng()
        dest = self.get_random_latlng()
        rider = self.rider_ctor(src=src, dest=dest,
                                **self.rider_params)
        event = RequestDispatchEvent(ts=ts, rider=rider)
        return [event]
