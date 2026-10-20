#!/bin/bash
#SBATCH --job-name=synthetic_generation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --hint=nomultithread
#SBATCH --time=20:00:00
#SBATCH --output=./logs_slurm/synthetic_generation.out
#SBATCH --error=./logs_slurm/synthetic_generation.err
#SBATCH --account=oou@h100
#SBATCH --constraint=h100

# A lancer depuis src/synthetic_generation/ (imports non qualifiés), après
# mkdir -p logs_slurm (Slurm ouvre les logs avant le début du script) :
#   sbatch generate.slurm                       # corpus complet (45 000 prompts)
#   sbatch generate.slurm --nb_prompts 1000 --output ../../outputs/synthetic_proto.json
# Relancer la même commande après un crash reprend au dernier chunk terminé.
# Enchaîne pre_clean.py puis dedup.py (seuil 0.9) : <output>_clean.json, <output>_clean_dedup.json.

module purge
module load arch/h100
module load cuda/12.8.0
module load python/3.11.5

source ../../.venv/bin/activate

PYTHON_INCLUDE_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_paths()['include'])")
export CPATH=$PYTHON_INCLUDE_DIR:$CPATH
export HF_HOME=/lustre/fswork/projects/rech/oou/uid39ok/.cache/huggingface
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TIKTOKEN_ENCODINGS_BASE=$HOME/tiktoken_encodings
export XDG_CACHE_HOME=$HOME/.cache
export VLLM_USE_TRITON_SAMPLER=0
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

nvidia-smi || exit 1

srun --gres=gpu:1 python3 generate.py "$@" || exit 1

# Nettoyage + déduplication sémantique de la sortie (comme clean.sh), avec un seuil
# plus strict que pour les corpus réels : les phrases générées sont plus proches entre elles.
DEDUP_THRESHOLD=0.9
OUTPUT=../../outputs/synthetic-fr_sentences.json
args=("$@")
for i in "${!args[@]}"; do
    case "${args[$i]}" in
        --output) OUTPUT="${args[$((i + 1))]}" ;;
        --output=*) OUTPUT="${args[$i]#--output=}" ;;
    esac
done
OUTPUT=$(realpath "$OUTPUT")

# pre_clean.py et dedup.py utilisent des imports non qualifiés
cd ../panta_picto_filter
python3 pre_clean.py "$OUTPUT" || exit 1
srun --gres=gpu:1 python3 dedup.py "${OUTPUT%.json}_clean.json" --threshold "$DEDUP_THRESHOLD"
