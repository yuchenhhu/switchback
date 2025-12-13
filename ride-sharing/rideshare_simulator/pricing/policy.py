from abc import ABC, abstractmethod
from typing import Callable

import pandas as pd

from ..state import WorldState
from .offer import Offer
from ..routing import get_route
from ..experiments import ExperimentPolicy


class PricingPolicy(ABC):
    def __init__(self):
        self.log = []

    def log_df(self):
        return pd.DataFrame(self.log)

    @abstractmethod
    def make_offer(self, dispatch) -> Offer:
        """
        Offers a price and an ETD guarantee to a customer.
        """
        raise NotImplementedError()


class ConstantFactorPricingPolicy(PricingPolicy):
    def __init__(self, price_factor: float,
                 etd_factor: float,
                 cost_fn: Callable,
                 dispatcher=None,
                 cost_basis="solo",
                 pickup_eta=900):
        super(ConstantFactorPricingPolicy, self).__init__()
        self.price_factor = price_factor
        self.etd_factor = etd_factor
        self.cost_fn = cost_fn
        self.cost_basis = cost_basis
        self.pickup_eta = pickup_eta

    def make_offer(self, dispatch) -> Offer:
        """
        Computes the ETD and cost to fulfill the request, and returns
        an offer with ETD and cost multiplied by a constant factor.

        `self.cost_basis` determines the type of (hypothetical) dispatch
        used to compute the cost of fulfilling the request:

        - "solo" dispatches the rider directly to their destination.
        - "greedy" finds the minimum cost dispatch given current supply.
        """
        # make an offer according to the expected route
        # having pool driver enjoys a discount
        if dispatch is None:
            return Offer(None, None, None)
        else:
            route = dispatch[1]
            etd = route.total_secs
            cost = self.cost_fn(route)
    
            return Offer(etd * self.etd_factor, cost * self.price_factor, dispatch[2])
