from dataclasses import dataclass
from math import floor
from typing import Any, Callable

from funcy.funcs import identity
import pandas as pd

from .utils import id_to_treatment
from .events import Event

@dataclass(frozen=True)
class Experiment:
    p: float = 0.5
    salt: str = ""
    attrgetter: Callable = identity

    def id_to_treatment(self, id):
        return id_to_treatment(id, self.p, self.salt)

    def is_treated(self, obj: Event):
        return self.id_to_treatment(self.attrgetter(obj))


@dataclass(frozen=True)
class SwitchbackExperiment(Experiment):
    interval: float=1.

    def is_treated(self, obj: Event):
        ts = self.attrgetter(obj)
        assert type(ts) == int or type(ts) == float
        return self.id_to_treatment(str(floor(ts / self.interval))) # str(floor(ts / self.interval)) generate block index


@dataclass
class ExperimentPolicy:
    expt: Experiment
    A: Any
    B: Any

    def is_treated(self, obj: Event):
        return self.expt.is_treated(obj)

    def get_policy(self, obj: Event):
        return self.get_policy_for_treatment(self.is_treated(obj))

    def get_policy_for_treatment(self, is_treated: bool):
        return self.B if is_treated else self.A

    @classmethod
    def ABExperiment(cls, A, B, p=0.5, salt=""):
        return cls(Experiment(p=p, salt=salt), A, B)

    @classmethod
    def SwitchbackExperiment(cls, A, B, p=0.5, salt="", interval=1.):
        return cls(SwitchbackExperiment(p=p, salt=salt, interval=interval),
                   A, B)

    def log_df(self):
        Adf = self.A.log_df()
        Adf["is_treated"] = False
        Bdf = self.B.log_df()
        Bdf["is_treated"] = True
        return pd.concat([Adf, Bdf])
