#!/bin/bash

# Submit the pre-processor
JOB1=$(sbatch --parsable $MULTISCALE_SCRIPTS/slurm/CUPRAD_pre_processor.slurm)

# Submit the main job when the pre-processor is finished
JOB2=$(sbatch --parsable --dependency=afterok:$JOB1 $MULTISCALE_SCRIPTS/slurm/CUPRAD.slurm)

JOB3=$(sbatch --parsable --dependency=afterok:$JOB2 $MULTISCALE_SCRIPTS/slurm/CTDSE_prepare_MPI.slurm)

# Run TDSE
JOB4=$(sbatch --parsable --dependency=afterok:$JOB3 --ntasks=1800 $MULTISCALE_SCRIPTS/slurm/MPI_CTDSE.slurm)

# Collect & merge data
JOB5=$(sbatch --parsable --dependency=afterok:$JOB4 $MULTISCALE_SCRIPTS/slurm/CTDSE_merge_hdf5.slurm)

# Run Hankel
JOBH1=$(sbatch --dependency=afterok:$JOB5 $MULTISCALE_SCRIPTS/slurm/Hankel_multiprocessing.slurm)