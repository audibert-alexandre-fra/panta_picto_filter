#!/bin/bash
#SBATCH --job-name=First_Training_STT_eval
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --hint=nomultithread
#SBATCH --time=00:10:00
#SBATCH --output=./logs_slurm/cosmo_annotated_chunk_0_eval.out
#SBATCH --error=./logs_slurm/cosmo_annotated_chunk_0_eval.err
#SBATCH --account=oou@h100
#SBATCH --constraint=h100

module purge
module load arch/h100
module load cuda/12.8.0
module load python/3.11.5

source ../../.venv/bin/activate

# --- Fix Python.h introuvable lors de la compilation JIT Triton ---
# On calcule le chemin d'include correspondant AU python réellement actif
# dans le venv, au lieu de pointer en dur vers un env anaconda qui ne
# correspond pas forcément à l'interpréteur utilisé.
PYTHON_INCLUDE_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_paths()['include'])")
echo "PYTHON_INCLUDE_DIR=$PYTHON_INCLUDE_DIR"
ls "$PYTHON_INCLUDE_DIR" | grep -i Python.h || echo "ATTENTION: Python.h absent de $PYTHON_INCLUDE_DIR"

export CPATH=$PYTHON_INCLUDE_DIR:$CPATH
export HF_HOME=/lustre/fswork/projects/rech/oou/uid39ok/.cache/huggingface
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TIKTOKEN_ENCODINGS_BASE=$HOME/tiktoken_encodings
export XDG_CACHE_HOME=$HOME/.cache

echo "CPATH=$CPATH"

export VLLM_USE_TRITON_SAMPLER=0

# Si Python.h reste introuvable malgré tout, décommenter cette ligne pour
# forcer vLLM à éviter la compilation JIT Triton (perte de perf, mais ça tourne) :
# export VLLM_ENFORCE_EAGER=1

# S'assurer que la libcuda du driver et la libcudart du toolkit sont visibles
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

# Détection du GPU alloué par SLURM (sinon srun sur un noeud sans GPU visible)
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

# Diagnostic : le GPU doit être listé ici, sinon il n'y a pas d'allocation GPU
nvidia-smi || exit 1
python3 -c "import torch; print('torch.cuda.is_available =', torch.cuda.is_available()); print('n_gpus =', torch.cuda.device_count())"

srun --gres=gpu:1 python3 filtering_picto.py cosmo_annotated_chunk_0.parquet 
