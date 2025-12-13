from heapq import heappush, heappop
import itertools as it
import pickle
from warnings import warn
from typing import List, Tuple

import funcy as f
import numpy as np
import pandas as pd
import rtree
import copy

from rideshare_simulator.events import Event

from .driver import Driver
from .routing import get_route
from .routing.waypoint import TripWaypoint, Waypoint
from .utils import point_to_box


class DriverIndex(dict):
    def __init__(self, drivers: List[Driver]):
        super(DriverIndex, self).__init__(
            {driver.id: driver for driver in drivers})
        self.update(0.)

    def add(self, ts: float, driver: Driver):
        self[driver.id] = driver
        latlng = driver.latlng(ts)
        self.tree.insert(hash(driver.id), latlng + latlng, obj=driver)

    def get_nearest_drivers(self, latlng: Tuple[float, float], n: int) -> List[Driver]:
        return list(self.tree.nearest(latlng, n, objects="raw"))

    def update(self, ts):
        "Cleans up offline drivers and updates the spatial index."
        self.clean_up_drivers()
        gtor = ((hash(driver.id), point_to_box(driver.latlng(ts)), driver)
                for driver in self.values()
                if driver.is_available(ts))
        try:
            self.tree = rtree.index.Index(gtor)
        except rtree.exceptions.RTreeError:
            warn("Rtree error.")
            self.tree = rtree.index.Index()

    def clean_up_drivers(self):
        to_clean = [id for (id, driver) in self.items()
                    if not driver.is_online]
        for id in to_clean:
            self.pop(id)


class WorldState(object):
    def __init__(self, drivers=None, update_interval=60):
        """
        :param update_interval
          Update the spatial index every `update_interval` seconds.
        """
        self.ts = 0
        self.last_update = 0
        self.update_interval = update_interval
        if drivers is None:
            self.drivers = {'A': DriverIndex([]),
                           'B': DriverIndex([]),
                           'expt': DriverIndex([])} 
        else: 
            self.drivers = {'A': drivers,
                           'B': drivers,
                           'expt': drivers} 
        self.riders = dict()
        self.event_queue = []

    @classmethod
    def from_pickle(cls, fname: str):
        with open(fname, "rb") as file:
            state = pickle.load(file)
        state.drivers.update(state.ts)  # Update the spatial index
        return state

    def step(self, ts: int):
        "Step forward in time to new ts."
        assert ts >= self.ts
        self.ts = ts

        # Update spatial index at fixed intervals.
        if self.ts - self.last_update > self.update_interval:
            self.last_update = self.ts
            for policy in ['A','B','expt']:
                self.drivers[policy].update(self.ts)

    def push_event(self, event: Event):
        return heappush(self.event_queue, event)

    def pop_event(self):
        return heappop(self.event_queue)

    def add_driver(self, driver: Driver):
        driver_copy_A = copy.deepcopy(driver)
        driver_copy_B = copy.deepcopy(driver)
        self.drivers['A'].add(self.ts, driver_copy_A)
        self.drivers['B'].add(self.ts, driver_copy_B)
        self.drivers['expt'].add(self.ts, driver)

    def get_rider(self, rider_id):
        return self.riders[rider_id]

    def get_matching_drivers(self, policy, pred):
        return list(filter(pred, self.drivers[policy].values()))

    def get_available_drivers(self, policy):
        return self.get_matching_drivers(policy, lambda d: d[policy].is_available)

    def get_nearest_drivers(self, policy, latlng: Tuple[float, float], n=1) -> List[Driver]:
        "Gets the n nearest drivers to latlng, regardless of driver status."
        return self.drivers[policy].get_nearest_drivers(latlng, n)

    def as_df(self):
        "Dump driver locations and routes to a DataFrame, for further analysis."
        current = ({'ts': self.ts,
             'driver_id': driver.id,
             'rider_id': None,
             'world_line': world_line,
             'wp_id': 0,
             'wp_type': 'current',
             'lat': driver.latlng(self.ts)[0],
             'lng': driver.latlng(self.ts)[1]}
            for world_line, drivers in self.drivers.items()
            for driver in drivers.values()
            if driver.is_online)
        
        future = ({'ts': self.ts,
             'driver_id': driver.id,
             'rider_id': (wp.rider_id if isinstance(wp, TripWaypoint) else None),
             'world_line': world_line,
             'wp_id': i + 1,
             'wp_type': wp.__class__.__name__,
             'lat': wp.latlng[0],
             'lng': wp.latlng[1]}
            for world_line, drivers in self.drivers.items()
            for driver in drivers.values()
            for (i, wp) in enumerate(driver.route.remaining_waypoints(self.ts))
            if driver.is_online)

        return pd.DataFrame(it.chain(current, future))
