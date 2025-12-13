from datetime import datetime
import os.path
from urllib.request import urlretrieve
from uuid import uuid4
from funcy.objects import cached_property

from pandas._libs.tslibs import nattype

import shapefile
import pandas as pd
import numpy as np

from ..events import RequestDispatchEvent, DriverOnlineEvent
from .rider_generator import RequestGenerator
from .driver_generator import DriverOnlineGenerator
from ..rider import MaxUtilityRider
from ..driver import Driver
from ..state import WorldState


class NYCTaxiGenerator(object):
    def __init__(self, trips_df: pd.DataFrame, shp,
                 method="actual", rel_rate=1.):
        """
        Generates events based on a DataFrame from the NYC TLC Taxi
        Dataset.

        :param method
           "actual" (i.e. in same order as dataset) or "uniform"
           (randomly sampled from dataset)
        :param rel_rate
           Rate at which events are produced, relative to the rate at
           which events appear in the dataset. Must be in [0, 1] if
           method == "actual"
        """
        self.trips_df = trips_df
        self.shp = shp
        self.method = method
        self.rel_rate = rel_rate
        self.next_index = 0

    @staticmethod
    def cache_file(fname, url, data_dir="data/"):
        cache_fname = os.path.join(data_dir, fname)
        if not os.path.exists(cache_fname):
            print(f"Retrieving {url} and caching in {cache_fname}...")
            urlretrieve(url, cache_fname)
        return cache_fname

    @classmethod
    def from_file(cls, trips_fname, shp_fname, **kwargs):
        df = pd.read_csv(trips_fname)
        df = df[df.pickup_latitude != 0.].reset_index()
        # Ensure that no two requests occur at exactly the same time
        df.tpep_pickup_datetime = (
            pd.to_datetime(df.tpep_pickup_datetime)
            .apply(datetime.timestamp)
            + np.random.rand(len(df)))
        df.tpep_dropoff_datetime = (
            pd.to_datetime(df.tpep_dropoff_datetime)
            .apply(datetime.timestamp))
        shp = shapefile.Reader(shp_fname)
        df = (df
              .sort_values(by=['tpep_pickup_datetime'], ascending=True)
              .reset_index(drop=True))
        return cls(df, shp, **kwargs)

    @classmethod
    def from_month(cls, yyyy: int, mm: int, data_dir="data/", **kwargs):
        "Caches the NYC TLC data (if not already cached) and loads into memory."
        if yyyy >= 2016:
            raise Exception(
                "Currently only supports pre-2016 data, which has exact"
                " pickup and dropoff latlngs.")
        url_base = "http://s3.amazonaws.com/nyc-tlc/"
        fname = f"yellow_tripdata_{yyyy:04d}-{mm:02d}.csv"
        trips_fname = cls.cache_file(
            fname, url=url_base + "trip+data/" + fname, data_dir=data_dir)
        shp_fname = cls.cache_file(
            "taxi_zones.zip",
            url=url_base + "misc/taxi_zones.zip",
            data_dir=data_dir)
        return cls.from_file(trips_fname, shp_fname, **kwargs)

    @cached_property
    def nominal_rate(self):
        "Trips per second in self.trips_df"
        return (len(self.trips_df) /
                (np.max(self.trips_df.tpep_pickup_datetime)
                 - np.min(self.trips_df.tpep_pickup_datetime)))

    def row_to_event(self, ts: float, row: pd.Series):
        raise NotImplementedError()

    def set_min_ts(self, ts):
        if self.trips_df.loc[self.next_index].tpep_pickup_datetime <= ts:
            self.next_index = np.argmax(self.trips_df.tpep_pickup_datetime > ts)

    def generate(self, state: WorldState):
        self.set_min_ts(state.ts)
        if self.method == "actual":
            self.next_index += np.random.geometric(self.rel_rate)
            next_ts = (self.trips_df.loc[self.next_index]
                       .tpep_pickup_datetime)
        elif self.method == "uniform":
            self.next_index = np.random.choice(len(self.trips_df))
            next_ts = state.ts + np.random.exponential(
                1 / (self.rel_rate * self.nominal_rate))
        else:
            raise NotImplementedError()

        if self.next_index >= len(self.trips_df):
            events = []
        else:
            next_row = self.trips_df.loc[self.next_index]
            events = [self.row_to_event(next_ts, next_row)]
        return events


class NYCTaxiRequestGenerator(NYCTaxiGenerator, RequestGenerator):
    def __init__(self, trips_df, shp,
                 mean_wtp_per_sec=0.01,
                 sigma=1., **kwargs):
        super(NYCTaxiRequestGenerator, self).__init__(
            trips_df, shp, **kwargs)
        self.mu = np.log(mean_wtp_per_sec)
        self.sigma = sigma

    def row_to_event(self, ts: float, row: pd.Series):
        "Convert a row from the trips dataset into a RequestDispatchEvent."
        wtp = np.random.lognormal(self.mu, self.sigma)
        v_taxi = (- row.fare_amount
                  - wtp * (row.tpep_dropoff_datetime -
                           row.tpep_pickup_datetime))
        rider = MaxUtilityRider(
            id=str(uuid4()),
            src=(row.pickup_latitude, row.pickup_longitude),
            dest=(row.dropoff_latitude, row.dropoff_longitude),
            wtp_per_sec=wtp, v_no_purchase=v_taxi)
        return RequestDispatchEvent(ts=ts, rider=rider)


class NYCTaxiDriverOnlineGenerator(NYCTaxiGenerator, DriverOnlineGenerator):
    def __init__(self, trips_df, shp, capacity=2,
                 mean_shift_length=float("Inf"), **kwargs):
        super(NYCTaxiDriverOnlineGenerator, self).__init__(
            trips_df, shp, **kwargs)
        self.capacity = capacity
        self.mean_shift_length = mean_shift_length

    def row_to_event(self, ts: float, row: pd.Series):
        "Convert a row from the trips dataset into a DriverOnlineEvent."
        shift_length = np.random.exponential(self.mean_shift_length)
        driver = Driver(latlng=(row.pickup_latitude, row.pickup_longitude),
                        capacity=self.capacity)
        return DriverOnlineEvent(ts=ts,
                                 driver=driver,
                                 shift_length=shift_length)
