# Switchback Experiments under Geometric Mixing

Code for reproducing the numerical experiments in Hu and Wager (2022).

## Reproducing the Simple Illustration

Folder Structure:
- `simple-illustration/`: Code used to reproduce the results in Sections 5.1 and C.1 of Hu and Wager (2022)
  - `sim_naive_dm.jl`: Evaluates the performance of the naive difference-in-means estimator
  - `sim_burn_in.jl`: Evaluates the performance of the difference-in-means estimator with burn-ins and the bias-corrected estimator
  - `analysis.R`: Reproduces the figures presented in Section 5.1 using outputs from the simulation scripts
  - `jackknife.ipynb`: Reproduces Tables 1, S2, and S3, and simulates the distributions of the ratios between estimated and true variances for the three estimators
  - `var_plot.r`: Reproduces Figure S2 using outputs from `jackknife.ipynb`

`sim_naive_dm.jl` and `sim_burn_in.jl` are designed to be run as SLURM array jobs with `array = 1–7`.
 
 ## Reproducing the Ride-Sharing Simulation

Folder Structure:
- `ride-sharing/`: Code used to reproduce the results in Sections 5.2 and C.2 of Hu and Wager (2022)
  - `config/default_taxi.yaml`: Experiment configurations, including the block length (i.e., switchback interval). The default is set to 4000 seconds.
  - `data/`: Taxi datasets used to simulate the ride-sharing process. Before running the simulator, add the 2015 taxi dataset `2015_Yellow.csv` to this folder.
  - `rideshare_simulator/`: Main code for simulating the ride-sharing process (details provided in Section C.3 of Hu and Wager (2022)).
  - `run_taxi.py`: Runs the ride-sharing simulator according to the configurations. Produces a file `summary.csv` in the `output/` directory summarizing the realized ride-sharing trajectory as well as the always-treated and always-control counterfactual trajectories.
  - `clean.R`: Cleans outputs from the `output/` directory and writes three cleaned files, `treatment.csv`, `control.csv`, and `actual.csv`, to `output/cleaned_files/`. Also computes the target estimand GATE and reproduces Figure 4.
  - `analysis.ipynb`: Reads results from `output/cleaned_files/` and reproduces Tables 2 and S4 (on estimators discussed in Hu and Wager (2022)). Also generates the results used to plot Figure 5 (right panel).
  - `results.R`: Reproduces Figure 5 and Tables 2 (second part) and S4 (on HT-type estimator comparison).

To run the ride-sharing simulation:
1. Download the ride-sharing simulator from Farias et al. (2022) and install the package following their instructions.  
2. Replace the folders `config/`, `data/`, and `rideshare_simulator/` in that package with the corresponding folders included in this repository.
3. Download the 2015 NYC taxi trip records dataset (Commission, N.D.), rename it to `2015_Yellow.csv`, and place it in the `data/` folder.
4. Add the other files and run `run_taxi.py` to generate the trajectories.
`run_taxi.py` is designed to be run as SLURM array jobs, where each run generates three coupled trajectories (one realized and two counterfactual).  

## References

Farias, V., Li, A., Peng, T., and Zheng, A. (2022).  
*Markovian Interference in Experiments.* In **Advances in Neural Information Processing Systems**, 35: 535–549.

Hu, Y. and Wager, S. (2022).  
**Switchback Experiments under Geometric Mixing.**  
Available at: https://arxiv.org/abs/2209.00197

New York City Taxi and Limousine Commission (N.D.).  
*TLC Trip Record Data.*  
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page  
(Accessed March 11, 2024).
