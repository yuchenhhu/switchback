from abc import ABC, abstractmethod
from typing import List, Tuple

import funcy as f
import pandas as pd

from rideshare_simulator.state import WorldState
from rideshare_simulator.events import RequestDispatchEvent
from rideshare_simulator.driver import Driver
from rideshare_simulator.routing import get_route
from ..routing.waypoint import Waypoint, PickupWaypoint, DropoffWaypoint
from ..routing.route import Route
from ..experiments import ExperimentPolicy


class DispatchPolicy(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def dispatch(self, state: WorldState, event: RequestDispatchEvent):
        raise NotImplementedError()


class CheapestDispatchPolicy(DispatchPolicy):
    def __init__(self, planner, knn=5, savings_threshold=1.):
        super(CheapestDispatchPolicy, self).__init__()
        self.knn = knn  ##consider the nearest knn drivers
        self.planner = planner
        self.savings_threshold = savings_threshold

    def get_candidates(self, policy, state: WorldState,
                       latlng: Tuple[float, float]) -> Tuple[List[Driver],
                                                             List[Driver]]:
        """
        Fetch up to knn pool drivers, and up to one idle driver.
        """
        nn = state.get_nearest_drivers(policy, latlng, self.knn * 4)
        eta = lambda driver: get_route(
            state.ts, [driver.latlng(state.ts), latlng]).total_secs
        candidates = sorted(nn, key=eta)

        is_idle = (lambda d: d.is_idle(state.ts) and
                   d.is_available(state.ts))
        idle_nn = f.take(1, filter(is_idle, candidates))

        is_pool = (lambda d: not d.is_idle(state.ts) and
                   d.is_available(state.ts))
        pool_nn = f.take(self.knn, filter(is_pool, candidates))
        return (idle_nn, pool_nn)

    def get_insertion(self, state: WorldState,
                      driver: Driver,
                      to_insert: List[Waypoint],
                      ub=float("Inf"),
                      enforce_etd=True):
        driver_latlng = driver.latlng(state.ts)
        remaining_wps = driver.route.remaining_trip_waypoints(state.ts)
        old_wps = [Waypoint(driver_latlng)] + remaining_wps
        old_route = get_route(state.ts, old_wps) if len(remaining_wps) > 0 \
            else Route.empty_route(state.ts, driver_latlng)
        old_cost = self.planner.cost(old_route)
        new_route = self.planner.optimize_plan(
            ts=state.ts,
            start_latlng=driver_latlng,
            plan=remaining_wps + to_insert,
            # ub=float("inf"))
            ub=ub + old_cost,
            enforce_etd=enforce_etd)
        insertion_cost = self.planner.cost(new_route) - old_cost
        return new_route, insertion_cost

    def dispatch(self, policy, state: WorldState, event: RequestDispatchEvent):
        rider = state.get_rider(event.rider_id)

        idle_nn, pool_nn = self.get_candidates(policy, state, rider.src)
        if len(idle_nn) == 0 and len(pool_nn) == 0:
            return []

        pickup = PickupWaypoint(rider.src, rider.id, float("Inf"))
        dropoff = DropoffWaypoint(rider.dest, rider.id)
        waypoints = [pickup, dropoff]

        if len(idle_nn) >= 1:
            best_route, idle_cost = self.get_insertion(
                state, idle_nn[0], waypoints, enforce_etd=False)
            best_driver = idle_nn[0]
            # Don't dispatch pool drivers unless savings
            # exceeds some threshold.
            best_cost = idle_cost * self.savings_threshold
        else:
            best_driver, best_route, best_cost = None, None, float("Inf")

        for driver in pool_nn:
            new_route, insertion_cost = self.get_insertion(
                state, driver, waypoints, ub=best_cost)
            if insertion_cost < best_cost:
                best_cost = insertion_cost
                best_driver = driver
                best_route = new_route

        if best_driver is None:
            return []
        is_idle = len(idle_nn) > 0 and best_driver == idle_nn[0]

        if is_idle:
            dispatches = [best_driver.id, best_route, is_idle, idle_cost]
        else:
            dispatches = [best_driver.id, best_route, is_idle, best_cost]

        return dispatches


class DispatchExperimentPolicy(ExperimentPolicy, DispatchPolicy):
    def dispatch(self, policy, state: WorldState, event: RequestDispatchEvent):
        is_treated = self.is_treated(event)
        dispatchA = self.A.dispatch(policy, state, event)
        dispatchB = self.B.dispatch(policy, state, event)
        return dispatchB if is_treated else dispatchA
