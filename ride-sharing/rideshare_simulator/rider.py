from dataclasses import dataclass, field
from typing import Tuple
import uuid

import numpy as np

from .pricing.offer import Offer
from .routing import get_route


@dataclass
class Rider(object):
    id: str
    src: Tuple[float, float]
    dest: Tuple[float, float]

    def respond_to_offer(self, offer: Offer) -> bool:
        return True


@dataclass
class MaxUtilityRider(Rider):
    wtp_per_sec: float
    v_no_purchase: float

    def respond_to_offer(self, offer: Offer) -> bool:
        v_purchase = - offer.etd * self.wtp_per_sec - offer.price
        #if offer.is_idle:
        return v_purchase > self.v_no_purchase
        #else:
            #return v_purchase*0.8 > self.v_no_purchase

    @classmethod
    def lognormal_utility(cls,
                          src: Tuple[float, float],
                          dest: Tuple[float, float],
                          cost_per_sec: float,
                          cost_per_km: float,
                          mean_wtp_per_sec: float,
                          sigma=1.,
                          pickup_eta=900):
        """
        Constructs a random MaxUtilityRider log-normally distributed
        willingness to pay per second, with parameters mu and sigma.
        Assumes that riders have access to an outside transportation option
        that takes them directly from source to destination.

        :param cost_per_sec Time cost of the rider's outside option.
        :param cost_per_km Dist. cost of the rider's outside option.
        :param mean_wtp_per_sec Mean WTP per second for riders.
        :param pickup_eta Bonus to the ETD of the outside option.
        """
        mu = np.log(mean_wtp_per_sec) - sigma ** 2 / 2
        wtp_per_sec = np.random.lognormal(mu, sigma)
        route = get_route(0., [src, dest])
        outside_cost = route.total_kms * cost_per_km + \
            (route.total_secs + pickup_eta) * (cost_per_sec + wtp_per_sec)
        return cls(id=str(uuid.uuid4()),
                   src=src,
                   dest=dest,
                   wtp_per_sec=wtp_per_sec,
                   v_no_purchase=-outside_cost)
