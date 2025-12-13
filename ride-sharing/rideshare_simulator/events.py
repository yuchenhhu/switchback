from dataclasses import dataclass
from functools import total_ordering

from .driver import Driver
from .rider import Rider
from .routing.route import Route
from .pricing.offer import Offer


# Events
# ------------------------------------------------------------------------
@dataclass(frozen=True)
@total_ordering
class Event(object):
    ts: float

    def __lt__(self, other):
        return self.ts < other.ts

@dataclass(frozen=True)
class DriverOnlineEvent(Event):
    driver: Driver
    shift_length: float

    @property
    def driver_id(self):
        return self.driver.id


@dataclass(frozen=True)
class DriverOfflineEvent(Event):
    driver_id: str

@dataclass(frozen=True)
class RequestDispatchEvent(Event):
    rider: Rider

    @property
    def rider_id(self):
        return self.rider.id


@dataclass(frozen=True)
class OfferResponseEvent(Event):
    policy: str
    treatment: int
    rider_id: Rider
    driver_id: str
    route: Route
    offer: Offer
    cost: float
    accepted: bool










