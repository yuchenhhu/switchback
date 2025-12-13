#!/bin/bash

#SBATCH --array=1-100             
#SBATCH -J python
#SBATCH -p normal
#SBATCH -n 1
#SBATCH -c 1                              
#SBATCH -t 5:00:00
##SBATCH --mem=1gb
#SBATCH -o rideshare-%A-%a.out

# Load software
module load anaconda3

srun python run_taxi.py
