from dataclasses import dataclass, field


@dataclass
class Offer(object):
    "Represents guarantees regarding a trip made to the rider."
    etd: float
    price: float
    is_idle: bool
