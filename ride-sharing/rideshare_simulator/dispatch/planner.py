from dataclasses import dataclass
import operator as op
from heapq import heappush, heappop
from typing import Callable, List, Tuple

import funcy as f

from ..routing import get_route
from ..routing.route import Route, RouteLeg
from ..routing.waypoint import Waypoint, DropoffWaypoint, PickupWaypoint


class ShortestPathNode:
    def __init__(self, plan: List[Waypoint],
                 route: Route,
                 rest: List[Waypoint],
                 cost: float):
        self.plan = plan
        self.route = route
        self.rest = rest
        self.cost = cost

    def __lt__(self, other):
        return self.cost < other.cost

    def __hash__(self):
        return hash(tuple(sorted(map(hash, self.plan))))

    @property
    def is_terminal(self):
        return len(self.rest) == 0

    def is_valid_plan(self, start_ts: float, enforce_etd=True):
        """
        Checks that
        """
        riders = set()
        is_valid = True
        ts = start_ts
        for leg in self.route.legs:
            if not is_valid:
                break
            ts += leg.secs
            if isinstance(leg.dest, PickupWaypoint):
                riders.add(leg.dest.rider_id)
            elif isinstance(leg.dest, DropoffWaypoint) :
                is_valid = (
                    is_valid and
                    # Dropoffs occur after pickups
                    (leg.dest.rider_id in riders) and
                    # ETD is respected (or explicitly ignored)
                    ((not enforce_etd) or
                     leg.dest.deadline >= ts))
        return is_valid


class ShortestPathPlanner(object):
    def __init__(self, cost: Callable[[Route], float]=op.attrgetter("total_kms")):
        self.cost = cost

    def add_waypoint(self, ts: float, path: ShortestPathNode,
                     waypoint: Waypoint):
        """
            add a point from "path.rest" subset to the end of the "path.plan"
        """
        route = get_route(ts, path.plan + [waypoint])
        rest_cp = [wp for wp in path.rest if wp != waypoint]
        return ShortestPathNode(
            plan=path.plan + [waypoint],
            route=route,
            rest=rest_cp,
            cost=self.cost(route))

    def optimize_plan(self, ts: float,
                      start_latlng: Tuple[float, float],
                      plan: List[Waypoint],
                      ub: float=float("Inf"),
                      enforce_etd=True) -> Route:
        """
        Finds the minimum-cost ordering of waypoints via Dijkstra
        (to solve a TSP problem), starting from start_latlng.

        If the minimum-cost ordering has cost > ub, or there is
        no feasible plan, then return a route with infinite cost.
        """
        pq = []
        path = ShortestPathNode(
            plan=[Waypoint(start_latlng)],
            route=Route.empty_route(ts, start_latlng),
            rest=plan, cost=0.)
        visited = set()
        heappush(pq, path)

        while not (path.is_terminal or len(pq) == 0 or path.cost > ub):
            path = heappop(pq)
            if path not in visited:
                visited.add(path)
                next_nodes = (self.add_waypoint(ts, path, next_wp)
                              for next_wp in path.rest)
                valid_nodes = filter(
                    lambda node: node.is_valid_plan(ts, enforce_etd=enforce_etd),
                    next_nodes)
                for node in valid_nodes:
                    heappush(pq, node)

        if path.is_terminal:
            route = get_route(ts, path.plan)
        else:
            # No feasible route
            route = Route(ts, [RouteLeg(Waypoint(start_latlng),
                                        Waypoint(start_latlng),
                                        float('Inf'), float('Inf'))])
        return route
