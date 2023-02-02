#!/bin/bash 
#SBATCH --nodes=1
#SBATCH --time=00:30:00
#SBATCH --job-name=openstudio
#SBATCH --partition=express
#SBATCH --mem=10G
#SBATCH --ntasks=28
#SBATCH --error=/work/able/resilience/Template/Outputs/%j.err
#SBATCH --output=/work/able/resilience/Template/Outputs/%j.out
module load anaconda3/2022.05
module load singularity/3.5.3
source activate kg_env_310
python run_simulations.py
