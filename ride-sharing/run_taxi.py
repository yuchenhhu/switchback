from datetime import datetime
from functools import reduce
import itertools as it
import json
import os
import operator as op
import pickle
import pathlib
import sys

import pandas as pd
import funcy as f
from tqdm import tqdm

import random
import yaml

from rideshare_simulator.dispatch.dispatch_policy import \
    CheapestDispatchPolicy, DispatchExperimentPolicy
from rideshare_simulator.dispatch.planner import ShortestPathPlanner
from rideshare_simulator.generators.driver_generator import UniformDriverOnlineGenerator
from rideshare_simulator.generators.rider_generator import UniformRequestGenerator
from rideshare_simulator.generators.taxi import \
    NYCTaxiRequestGenerator, NYCTaxiDriverOnlineGenerator
from rideshare_simulator.rider import MaxUtilityRider
from rideshare_simulator.pricing.policy import ConstantFactorPricingPolicy
from rideshare_simulator.simulator import Simulator
from rideshare_simulator.state import WorldState
from rideshare_simulator.summary import RequestSummarizer, StateSummarizer
from rideshare_simulator.experiments import Experiment, SwitchbackExperiment

seed = os.environ.get('SLURM_ARRAY_TASK_ID')

config_file = "config/default_taxi.yaml"

# Read configurations from the YAML file
with open(config_file, "r") as file:
    configurations = yaml.safe_load(file)

min_latlng = (37.736927, -122.512273)
max_latlng = (37.816437, -122.375974)
rider_params = configurations['rider']
driver_params = configurations['driver']

def request_generator(rider, min_ts, cost_per_km, cost_per_sec):
    if rider["generator"] == "uniform":
        rider_params = dict(mean_wtp_per_sec=rider['mean_wtp_per_sec'],
                            cost_per_km=cost_per_km,
                            cost_per_sec=cost_per_sec)
        gen = UniformRequestGenerator(
            rider['mean_time'],
            min_latlng, max_latlng,
            rider_ctor=MaxUtilityRider.lognormal_utility,
            rider_params=rider_params)
    elif rider["generator"] == "taxi":
        gen = NYCTaxiRequestGenerator.from_file(
            rider['trips_fname'],
            rider['shp_fname'],
            mean_wtp_per_sec=rider['mean_wtp_per_sec'],
            sigma=rider['sigma'],
            rel_rate=rider['rel_rate'],
            method=rider['method'])
        gen.set_min_ts(min_ts)
    else:
        raise NotImplementedError()
    return gen

def driver_generator(driver, min_ts):
    if driver["generator"] == "uniform":
        gen = UniformDriverOnlineGenerator(
            driver["mean_time"], min_latlng, max_latlng,
            mean_shift_length=driver["mean_shift_length"],
            capacity=driver["capacity"])
    elif driver["generator"] == "taxi":
        gen = NYCTaxiDriverOnlineGenerator.from_file(
            driver['trips_fname'],
            driver['shp_fname'],
            capacity=driver['capacity'],
            rel_rate=driver['rel_rate'],
            mean_shift_length=driver['mean_shift_length'],
            method=driver['method'])
        gen.set_min_ts(min_ts)
    else:
        raise NotImplementedError()

    return gen

request_gen = request_generator(rider_params,
                                configurations['min_ts'],
                                configurations['cost_per_km'],
                                configurations['cost_per_sec'])
driver_gen = driver_generator(driver_params,
                             configurations['min_ts'])

def cost_fn(cost_per_km, cost_per_sec):
    return lambda route: cost_per_km * route.total_kms + \
        cost_per_sec * route.total_secs

def my_experiment(experiment, seed):
    configs = dict(ab=(Experiment, "rider_id"),
                   switchback=(SwitchbackExperiment, "ts"))
    ctor, attr = configs[experiment["type"]]
    return ctor(salt=experiment["salt"] + str(seed),
                attrgetter=op.attrgetter(attr),
                **f.omit(experiment, ["type", "salt"]))

def dispatch_policy_A(dispatch):
    planner = ShortestPathPlanner(cost=cost_fn(configurations['cost_per_km'],configurations['cost_per_sec']))
    return CheapestDispatchPolicy(planner, dispatch['knn'], dispatch['savings_threshold'])

def dispatch_policy_B(dispatch):
    planner = ShortestPathPlanner(cost=cost_fn(configurations['cost_per_km'],configurations['cost_per_sec']))
    return CheapestDispatchPolicy(planner, dispatch['knn'], dispatch['savings_threshold'])

def dispatch_policy_expt(dispatch, experiment, seed):
    planner = ShortestPathPlanner(cost=cost_fn(configurations['cost_per_km'],configurations['cost_per_sec']))
    A = CheapestDispatchPolicy(planner, **dispatch["A"])
    B = CheapestDispatchPolicy(planner, **dispatch["B"])
    return DispatchExperimentPolicy(my_experiment(experiment, seed), A, B)

dispatcher_A = dispatch_policy_A(configurations['dispatch']['A'])
dispatcher_B = dispatch_policy_A(configurations['dispatch']['B'])
dispatcher_expt = dispatch_policy_expt(configurations['dispatch'],configurations['experiment'], seed)

pricing_params = configurations['pricing']
pricer = ConstantFactorPricingPolicy(
    cost_fn=cost_fn(configurations['cost_per_km'],configurations['cost_per_sec']), 
    price_factor=pricing_params['price_factor'],
    etd_factor=pricing_params['etd_factor'],
    cost_basis=pricing_params['cost_basis'])

random.seed(seed)

sim = Simulator(request_gen, driver_gen, dispatcher_A, dispatcher_B, dispatcher_expt, pricer)

T = configurations['T']
summ = RequestSummarizer()
summary = summ.init()
for state, events in sim.run(T):
    summary = summ.reducer(summary, (state, events))

df = summ.finish(summary)
df.to_csv(f"output/summary{seed}.csv", index=False)


