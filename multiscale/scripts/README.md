# Collection of scipts to maintain the execution of MMA

The execution of the whole model is done through [***the pipeline***](../../README.md#execution-pipeline). Here is a collection of scripts used to orchestrate the pipeline within the [SLURM scheduler](https://hpc-wiki.info/hpc/SLURM).

***Important notes:***
* Each computational cluster might have different requirements for the slurm commands depending on their architecture (partitions, resource management, constraints such a number of tasks, etc.). These scripts shall be then taken as templates and adapted for the particular environments according to documentations of the machine.
* Each simulation must be executed in its own directory because there are some auxiliary temporary files withthe same names created. After the simulations are done, everything is stored in the hdf5 archive. The results might be then organised afterwards.
* Each job requires [the same modules](../../README.md#modules-and-libraries) as the corresponing binary. It is assumed to be done through environment functions [`../../Modules/load_modules.sh`](../../Modules/load_modules.sh).


## `run_multiscale.sh`
This is an example of a script to execute the whole pipeline. The particular slurm scripts are referred from this script. Note that the number of nodes is specified in this script by `--ntasks=1800` in

    JOB4=$(sbatch --parsable --dependency=afterok:$JOB3 --ntasks=1800 $MULTISCALE_SCRIPTS/slurm/MPI_CTDSE.slurm)
This is the number of MPI processes. The number of nodes used for the calculation is usually $\lceil$`ntasks`/ "CPUs per node" $\rceil$, which depends on a given architecture of each HPC. From our experience, slurm is capable to set other parameters automatically when only `ntasks` is provided.


## `gas_cell_scan.sh`
This is a higher order script to do a simple parametric scan by running the multiscale model several times with one varying input. This variation is defined in a list of input hdf5-archives.

## `gas_cell_scan_txt.sh` (TO BE DONE)
This is the same as the previous script. The difference is that the inputs are parsed from a text-based inputs in the form described in https://github.com/vabekjan/universal_input.

## `slurm` scripts
This directory contain the templates of the slurm script & specific script for specific machines used so far.

