import cython
import bisect
from dataclasses import dataclass

import funcy as f
import numpy as np

from rideshare_simulator.utils import interpolate_latlng, clip
from .waypoint import Waypoint, TripWaypoint, DropoffWaypoint


class RouteLeg(object):
    def __init__(self, src: Waypoint, dest: Waypoint,
                 kms: cython.float, secs: cython.float):
        self.src = src
        self.dest = dest
        self.kms = kms
        self.secs = secs


class Route(object):
    def __init__(self, start_ts: cython.float, legs):
        self.start_ts = start_ts
        self.legs = legs
        self.waypoints = [leg.src for leg in legs] + [legs[-1].dest]
        self.total_kms = sum(leg.kms for leg in legs)
        self.total_secs = sum(leg.secs for leg in legs)
        self.leg_end_ts = (start_ts + np.cumsum([leg.secs for leg in legs])).tolist()

    @classmethod
    def empty_route(cls, start_ts, latlng):
        return cls(start_ts, [
            RouteLeg(Waypoint(latlng),
                     Waypoint(latlng), 0., 0.)])

    def current_leg(self, ts: cython.float):
        return bisect.bisect_right(self.leg_end_ts, ts)

    def current_leg_progress(self, ts: cython.float):
        "The proportion of the current leg that has been completed."
        leg_idx = self.current_leg(ts)
        leg_start_ts = self.leg_end_ts[leg_idx - 1] if leg_idx >= 1 else self.start_ts
        return clip((ts - leg_start_ts) /
                    (self.leg_end_ts[leg_idx] - leg_start_ts),
                    0., 1.)

    def latlng(self, ts: cython.float):
        if self.progress(ts) >= 1.:
            return self.legs[-1].dest.latlng
        else:
            leg = self.legs[self.current_leg(ts)]
            return interpolate_latlng(
                leg.src.latlng, leg.dest.latlng, self.current_leg_progress(ts))

    # @lru_cache(maxsize=1)
    def progress(self, ts: cython.float):
        if self.total_secs == 0.:
            return 1.
        else:
            return clip((ts - self.start_ts) /
                        (self.leg_end_ts[-1] - self.start_ts),
                        0., 1.)

    # @lru_cache(maxsize=1)
    def remaining_legs(self, ts: cython.float):
        if self.progress(ts) >= 1.:
            return []
        else:
            return self.legs[self.current_leg(ts):]

    def remaining_kms(self, ts: cython.float):
        # FIXME This only works if speed is constant.
        return self.total_kms * (1 - self.progress(ts))

    def remaining_secs(self, ts: cython.float):
        return self.total_secs * (1 - self.progress(ts))

    def is_complete(self, ts: cython.float):
        return ts >= self.leg_end_ts[-1]

    # @lru_cache(maxsize=1)
    def remaining_trip_waypoints(self, ts: cython.float):
        return [leg.dest for leg in self.remaining_legs(ts)
                if isinstance(leg.dest, TripWaypoint)]

    # @lru_cache(maxsize=1)
    def remaining_waypoints(self, ts: cython.float):
        return [leg.dest for leg in self.remaining_legs(ts)]

    # @lru_cache(maxsize=1)
    def remaining_riders(self, ts: cython.float):
        my_riders = set()
        for wp in self.remaining_trip_waypoints(ts):
            my_riders.add(wp.rider_id)
        return my_riders

    def slack_time(self, ts: cython.float):
        current: cython.int = self.current_leg(ts)
        slack = float("Inf")
        for (leg, end_ts) in zip(
                self.legs[current:], self.leg_end_ts[current:]):
            if isinstance(leg.dest, DropoffWaypoint):
                slack = min(slack, leg.dest.deadline - end_ts)
        return slack
