#!/bin/bash
#SBATCH --job-name=load_model
#SBATCH --partition=archive          # partition avec accès au STORE
#SBATCH --account=oou@cpu            # compte valide pour archive/cpu
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# --- Préparation de l'environnement ---
source .venv/bin/activate

# --- Exécution du chargement du modèle (cache) ---
python3 load_model.py --model "Qwen/Qwen3-14B"
