#!/bin/bash


export SUBMITTING_DIRECTORY=($pwd)
# Submit the first job
# JOB1=$(qsub $MULTISCALE_SCRIPTS/pbs/galdor/CUPRAD_pre_processor.pbs)

# Submit the main job when the first job is finished (depend=afterok)
# JOB2=$(qsub -W depend=afterok:$JOB1 $MULTISCALE_SCRIPTS/pbs/galdor/CUPRAD.pbs)


# Copy already pre-processed input
JOB1=$(qsub $MULTISCALE_SCRIPTS/pbs/galdor/copy_inps.pbs)

# run main CUPRAD code
JOB2=$(qsub -W depend=afterok:$JOB1 $MULTISCALE_SCRIPTS/pbs/galdor/CUPRAD.pbs)

## TDSE part

JOB3=$(qsub -W depend=afterok:$JOB2 $MULTISCALE_SCRIPTS/pbs/galdor/CTDSE_prepare_MPI.pbs)

# Include whatever resources you need either in the PBS script itself or via command-line options
JOB4=$(qsub -W depend=afterok:$JOB3 \
            -l select=2:ncpus=2:mem=16gb:scratch_local=16gb:cl_galdor=True \
            -l walltime=12:00:00 \
            $MULTISCALE_SCRIPTS/pbs/galdor/MPI_CTDSE.pbs)

# JOB4=$(qsub -W depend=afterok:$JOB3 \
#             -l select=10:ncpus=32:mem=16gb:scratch_local=100gb:cl_galdor=True \
#             -l walltime=48:00:00 \
#             $MULTISCALE_SCRIPTS/pbs/galdor/MPI_CTDSE.pbs)

JOB5=$(qsub -W depend=afterok:$JOB4 $MULTISCALE_SCRIPTS/pbs/galdor/CTDSE_merge_hdf5.pbs)

# # Run Hankel code after the merge completes
# JOBH1=$(qsub -W depend=afterok:$JOB5 $MULTISCALE_SCRIPTS/pbs/galdor/Hankel_multiprocessing.pbs)