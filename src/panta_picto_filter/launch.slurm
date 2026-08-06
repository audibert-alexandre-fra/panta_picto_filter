#!/bin/bash
#SBATCH --job-name=First_Training_STT
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --hint=nomultithread
#SBATCH --time=00:10:00
#SBATCH --output=./logs_slurm/cosmo_annotated_chunk_0_processed.out
#SBATCH --error=./logs_slurm/cosmo_annotated_chunk_0._processed.err
#SBATCH --account=oou@h100
#SBATCH --constraint=h100

module purge
module load arch/h100

source ../../.venv/bin/activate

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=$HOME/.cache/huggingface

python3 filtering_picto.py cosmo_annotated_chunk_0.parquet

