import argparse
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from utils import read_json, save_json


DEFAULT_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# At 0.95 tatoeba loses ~27% (tu/vous, il/elle, translation variants) while pairs
# with a different meaning only start to merge around 0.92.
DEFAULT_THRESHOLD: float = 0.95
# Neighbours examined per sentence: a cluster larger than this is only partly removed.
TOP_K: int = 16
EMBED_BATCH_SIZE: int = 1024
# 2048 x 1.9M (wikipedia) fp16 similarities on GPU ~ 8 GB of GPU memory.
QUERY_BATCH_SIZE: int = 2048


@torch.inference_mode()
def embed(texts: list[str], name_model: str, device: str) -> torch.Tensor:
    """Embed sentences with mean pooling, L2-normalised.

    Args:
        texts: Sentences to embed.
        name_model: Hugging Face sentence-transformers model.
        device: Torch device.

    Returns:
        A ``(len(texts), hidden_size)`` tensor on ``device`` (float16 on GPU, float32 on CPU).
    """
    tokenizer = AutoTokenizer.from_pretrained(name_model)
    model = AutoModel.from_pretrained(name_model).to(device).eval()
    dtype = torch.float16 if device == "cuda" else torch.float32
    model = model.to(dtype)

    # Sorting by length minimises padding; rows are written back in input order.
    order = np.argsort([len(text) for text in texts])
    embeddings = torch.empty((len(texts), model.config.hidden_size), dtype=dtype, device=device)
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        ids = order[i:i + EMBED_BATCH_SIZE]
        encoded = tokenizer(
            [texts[j] for j in ids], padding=True, truncation=True, max_length=128, return_tensors="pt"
        ).to(device)
        hidden = model(**encoded).last_hidden_state.float()
        mask = encoded["attention_mask"].unsqueeze(-1).float()
        pooled = (hidden * mask).sum(1) / mask.sum(1)
        embeddings[torch.from_numpy(ids).to(device)] = torch.nn.functional.normalize(pooled, dim=-1).to(dtype)
    return embeddings


@torch.inference_mode()
def nearest_neighbours(embeddings: torch.Tensor, top_k: int) -> tuple[np.ndarray, np.ndarray]:
    """Exact top-k cosine neighbours of every sentence (self excluded).

    Returns:
        ``(indices, similarities)``, both of shape ``(n, top_k)``, sorted by decreasing similarity.
    """
    n = embeddings.shape[0]
    top_k = min(top_k, n - 1)
    indices = np.empty((n, top_k), dtype=np.int64)
    similarities = np.empty((n, top_k), dtype=np.float32)
    for i in range(0, n, QUERY_BATCH_SIZE):
        sim = embeddings[i:i + QUERY_BATCH_SIZE] @ embeddings.T
        rows = torch.arange(sim.shape[0], device=sim.device)
        sim[rows, rows + i] = -1.0
        values, ids = sim.topk(top_k, dim=1)
        indices[i:i + QUERY_BATCH_SIZE] = ids.cpu().numpy()
        similarities[i:i + QUERY_BATCH_SIZE] = values.float().cpu().numpy()
    return indices, similarities


def greedy_dedup(indices: np.ndarray, similarities: np.ndarray, threshold: float) -> np.ndarray:
    """Order-preserving greedy dedup: each kept sentence removes its later near-duplicates.

    Returns:
        For every sentence, the index of the kept sentence that removed it, or ``-1`` if kept.
    """
    removed_by = np.full(len(indices), -1, dtype=np.int64)
    for i in range(len(indices)):
        if removed_by[i] != -1:
            continue
        for j, sim in zip(indices[i], similarities[i]):
            if sim < threshold:
                break
            if j > i and removed_by[j] == -1:
                removed_by[j] = i
    return removed_by


def dedup(
    dataset_path: str,
    threshold: float = DEFAULT_THRESHOLD,
    name_model: str = DEFAULT_MODEL,
    text_field: str = "text",
) -> None:
    """Remove semantic near-duplicates from a sentence corpus.

    Writes ``<name>_dedup.json`` (kept entries, unchanged) and ``<name>_dedup_removed.json``
    (removed sentences with the kept sentence they duplicate and their cosine similarity).

    Args:
        dataset_path: Path to the input ``.json`` file (list of dicts with ``text_field``).
        threshold: Cosine similarity above which two sentences are duplicates.
        name_model: Hugging Face sentence-transformers model.
        text_field: Field to embed.
    """
    name_dataset = dataset_path if dataset_path.endswith(".json") else f"{dataset_path}.json"
    data: list[dict] = read_json(name_dataset)
    texts = [entry[text_field] for entry in data]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    start = time.time()

    embeddings = embed(texts, name_model, device)
    print(f"Embedded {len(texts)} sentences on {device} in {time.time() - start:.0f}s")
    indices, similarities = nearest_neighbours(embeddings, TOP_K)
    print(f"Nearest neighbours done in {time.time() - start:.0f}s")
    removed_by = greedy_dedup(indices, similarities, threshold)

    kept = [entry for entry, by in zip(data, removed_by) if by == -1]
    removed = [
        {
            "text": texts[j],
            "duplicate_of": texts[by],
            "similarity": round(float((embeddings[j].float() @ embeddings[by].float()).item()), 4),
        }
        for j, by in enumerate(removed_by) if by != -1
    ]

    input_path = Path(name_dataset)
    save_json(path=str(input_path.with_name(f"{input_path.stem}_dedup.json")), data=kept)
    save_json(path=str(input_path.with_name(f"{input_path.stem}_dedup_removed.json")), data=removed)
    print(
        f"{input_path.name}: {len(data)} -> {len(kept)} "
        f"(-{len(removed)}, {len(removed) / max(len(data), 1):.1%}, threshold {threshold})"
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name_dataset``, ``threshold``, ``model`` and ``text_field``.
    """
    parser = argparse.ArgumentParser(description="Semantic deduplication with sentence embeddings")
    parser.add_argument("name_dataset", type=str)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--text_field", type=str, default="text")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    dedup(
        dataset_path=args.name_dataset,
        threshold=args.threshold,
        name_model=args.model,
        text_field=args.text_field,
    )
