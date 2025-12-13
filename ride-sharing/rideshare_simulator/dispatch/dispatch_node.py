from dataclasses import dataclass
from enum import Enum
from typing import Tuple


@dataclass
class Waypoint(object):
    latlng: Tuple[float, float]
    deadline = float("Inf")


@dataclass
class PickupWaypoint(Waypoint):
    rider_id: str


@dataclass
class DropoffWaypoint(Waypoint):
    rider_id: str


@dataclass
class RouteLeg(object):
    src: Waypoint
    dest: Waypoint
    distance: float
    time: float


@dataclass
class Route(object):
    legs: list[RouteLeg]


@dataclass
class RoutePointer(object):
    "Marks a specific position on a route."
    leg: int
    progress: float


def step_route(route: Route, ptr: RoutePointer, dts: float):
    "Step ptr forward in route by dts."
    time_to_dest = route.legs[ptr.leg].time * (1 - ptr.progress)
    if dts >= time_to_dest:
        if ptr.leg + 1 >= len(route.legs):
            return RoutePointer(ptr.leg, 1.)
        else:
            return step_route(
                route, RoutePointer(ptr.leg + 1, 0.), dts - time_to_dest)
    else:
        new_progress = ptr.progress + \
            (1 - ptr.progress) * dts / time_to_dest
        return RoutePointer(ptr.leg, new_progress)


def get_latlng(route: Route, ptr: RoutePointer):
    leg = route.legs[ptr.leg]
    return interpolate_latlng(
        leg.src.latlng, leg.dest.latlng, ptr.progress)


def interpolate_latlng(a, b, p):
    lata, lnga = a
    latb, lngb = b
    return (lata * p + latb * (1 - p)), (lnga * p + lngb * (1 - p))


def assigned_riders(route: Route, ptr: RoutePointer):
    return set([node.rider_id for node in plan[ptr.leg:]])


def pickups(plan: list[Waypoint]):
    return set([node.rider_id for node in plan
                if node.type == WaypointType.PICKUP])


def dropoffs(plan: list[Waypoint]):
    return set([node.rider_id for node in plan
                if node.type == WaypointType.DROPOFF])
