#!/bin/bash
#SBATCH --job-name=myjob         # create a short name for your job
#SBATCH --nodes=1                # node count
#SBATCH --ntasks=1               # total number of tasks across all nodes
#SBATCH --cpus-per-task=4        # cpu-cores per task (>1 if multi-threaded tasks)
#SBATCH --mem=64G              # total memory 
#SBATCH --gres=gpu:1             # number of gpus per node 
#SBATCH --time=1:00:00          # total run time limit (HH:MM:SS)


module purge
module load anaconda3/2024.2 
conda activate NL-env2

python compute_ref_metrics.py "$@"