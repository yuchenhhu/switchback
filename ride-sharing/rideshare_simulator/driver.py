from uuid import uuid4
from rideshare_simulator.routing.route import Route, RouteLeg


class Driver(object):
    def __init__(self, latlng, capacity=2, id=None):
        self.id = uuid4() if id is None else id
        self.route = Route.empty_route(0., latlng)
        self.max_capacity = capacity
        self.is_online = True

    def latlng(self, ts):
        return self.route.latlng(ts)

    def go_offline(self):
        self.is_online = False

    def has_capacity(self, ts):
        return self.capacity(ts) > 0

    def capacity(self, ts):
        return self.max_capacity - len(self.route.remaining_riders(ts))

    def is_available(self, ts):
        return self.is_online and self.has_capacity(ts)

    def is_idle(self, ts):
        return self.route.is_complete(ts)
