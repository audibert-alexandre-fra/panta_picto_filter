#!/bin/bash
#SBATCH --job-name=load_model
#SBATCH --partition=gpu_p4           # partition avec accès aux GPU
#SBATCH --account=oou@a100           # compte valide pour GPU
#SBATCH --gres=gpu:1                 # 1 GPU requis pour vLLM
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# --- Préparation de l'environnement ---
cd ..
source .venv/bin/activate
export PYTHONPATH="$PYTHONPATH:/lustre/fsn1/projects/rech/oou/uid39ok/picto_translation/nwsd/src"

# --- Exécution du chargement du modèle (cache) ---
python3 load_model.py --model "Qwen/Qwen3-14B"
