#!/bin/bash 
#SBATCH --nodes=1
#SBATCH --time=04:00:00
#SBATCH --job-name=redoHI
#SBATCH --partition=short
#SBATCH --mem=10G
#SBATCH --ntasks=28
#SBATCH --error=/work/able/resilience/Actual/Output/%j.err
#SBATCH --output=/work/able/resilience/Actual/Output/%j.out
#SBATCH --array=0-8%8

module load anaconda3/2022.05
# module load singularity/3.5.3
source activate kg_env_310
# python make_folders.py $SLURM_ARRAY_TASK_ID &&
# python baseline_files.py $SLURM_ARRAY_TASK_ID
# python outage_files.py $SLURM_ARRAY_TASK_ID &&
# python run_baselines.py $SLURM_ARRAY_TASK_ID 
# python run_outages.py $SLURM_ARRAY_TASK_ID &&
python post_process.py $SLURM_ARRAY_TASK_ID