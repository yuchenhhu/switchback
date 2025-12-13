from copy import copy
from dataclasses import dataclass
from singledispatchmethod import singledispatchmethod
from typing import Tuple

import funcy as f
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape, Point
from shapely.ops import transform

import rideshare_simulator.events as events
from rideshare_simulator.state import WorldState
from .routing import get_route
from .experiments import Experiment


class StateSummarizer(object):
    def __init__(self, interval=120.):
        super(StateSummarizer, self).__init__()
        self.interval = interval
        self.last_update = 0.

    def reducer(self, prev, update: Tuple[WorldState, events.Event]):
        state, event = update
        driver_df = state.as_df()
        if event.ts >= self.last_update + self.interval:
            self.last_update = event.ts
            prev.append(driver_df)
        return prev

    def finish(self, prev):
        return pd.concat(prev)

    def init(self):
        return []


class RequestSummarizer(object):
    def __init__(self):
        pass

    def reducer(self, summary, update: Tuple[WorldState, events.Event]):
        state, event = update
        result = self.summarize_event(event, state)
        if not result is None:
            summary.append(result)
        return summary

    def init(self):
        return []
        
    def finish(self, summary):
        return pd.DataFrame(summary)

    @singledispatchmethod
    def summarize_event(self, event, state):
        return None

    @summarize_event.register(events.OfferResponseEvent)
    def _(self, event: events.OfferResponseEvent, state):
        if event.offer.price is None:
            price = None
        else:
            price = event.offer.price*(0.5+event.offer.is_idle*0.5)
        summ = dict(ts=event.ts,
                    world_line=event.policy,
                    treatment=event.treatment,
                    rider_id=event.rider_id,
                    driver_id=event.driver_id,
                    etd=event.offer.etd,
                    price=price,
                    cost=event.cost,
                    is_idle=event.offer.is_idle,
                    accepted=event.accepted)
        return summ

