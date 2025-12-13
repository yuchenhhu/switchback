from functools import lru_cache

import cython
import funcy as f
import numpy as np

from .route import Route, RouteLeg
from .waypoint import Waypoint
from ..utils import isalatlng
from .haversine import fast_haversine


class RoutingEngine(object):
    def route_pair(self, src: Waypoint, dest: Waypoint):
        raise NotImplementedError()

    def route(self, ts: float, wps) -> Route:
        """
            concat pairwise routes:
                (point1 -> point2)
                (point2 -> point3)
                .... 
                (pointk-1 -> pointk)
            together from (point1, point2, ... pointk) in wps
        """
        if isinstance(wps[0], Waypoint):
            legs = f.lconcat(*(self.route_pair(src, dest)
                               for src, dest in f.pairwise(wps)))
            return Route(ts, legs)
        elif isalatlng(wps[0]):
            return self.route(ts, f.lmap(Waypoint, wps))
        else:
            raise NotImplementedError(
                "Input must be list of either Waypoints or (lat, lng).")


class HaversineRoutingEngine(RoutingEngine):
    def __init__(self, kmph=40.):
        self.kmps = kmph / 3600.

    @lru_cache(maxsize=512)
    def route_pair(self, src: Waypoint, dest: Waypoint):
        km = fast_haversine(*src.latlng, *dest.latlng)
        return [RouteLeg(src, dest, km, km / self.kmps)]


class EuclideanRoutingEngine(RoutingEngine):
    "For testing purposes only."
    def route_pair(self, src: Waypoint, dest: Waypoint):
        km = np.sqrt((src.latlng[0] - dest.latlng[0]) ** 2
                     + (src.latlng[1] - dest.latlng[1]) ** 2)
        return [RouteLeg(src, dest, km, km)]


HAVERSINE_ENGINE = HaversineRoutingEngine()
EUCLIDEAN_ENGINE = EuclideanRoutingEngine()

def get_route(ts: cython.float, wps, engine="haversine"):
    engines = dict(haversine=HAVERSINE_ENGINE,
                   euclidean=EUCLIDEAN_ENGINE)
    return engines[engine].route(ts, wps)
