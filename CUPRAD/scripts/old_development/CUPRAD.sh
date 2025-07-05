#!/bin/bash
#SBATCH --job-name="CUPRAD"
#SBATCH -t 0-01:00 # time (D-HH:MM)
#SBATCH -o CUPRAD.%j.%N.out # STDOUT
#SBATCH -e CUPRAD.%j.%N.err # STDERR
#SBATCH --profile=All

### Purge modules
module purge

### Load modules
load_modules

mpirun $CUPRAD_HOME/build/cuprad.e
