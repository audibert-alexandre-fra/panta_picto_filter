import argparse
import json
from collections import Counter


def distinct_n(token_lists: list[list[str]], n: int) -> float:
    """Ratio of distinct n-grams over all n-grams (1.0 = no repetition)."""
    ngrams = Counter(
        tuple(tokens[i:i + n]) for tokens in token_lists for i in range(len(tokens) - n + 1)
    )
    total = sum(ngrams.values())
    return len(ngrams) / total if total else 0.0


def report(dataset_path: str, top: int) -> None:
    """Print cheap diversity statistics of a generated corpus (CPU only).

    The real collapse measure is the share removed by dedup.py (run through clean.sh):
    above ~40%, the combinations in seeds.py should be enriched before scaling up.

    Args:
        dataset_path: Generated ``.json`` file.
        top: Number of most frequent sentence openings to show.
    """
    with open(dataset_path, "r", encoding="utf-8") as f:
        data: list[dict] = json.load(f)
    texts = [row["text"] for row in data]
    token_lists = [text.lower().split() for text in texts]

    print(f"Sentences          : {len(texts)}")
    print(f"Exact unique       : {len(set(texts))} ({len(set(texts)) / len(texts):.1%})")
    print(f"Mean length (words): {sum(map(len, token_lists)) / len(texts):.1f}")
    for n in (1, 2, 3):
        print(f"distinct-{n}         : {distinct_n(token_lists, n):.3f}")

    openings = Counter(" ".join(tokens[:2]) for tokens in token_lists)
    print(f"\nTop {top} openings (2 words):")
    for opening, count in openings.most_common(top):
        print(f"  {count:>7} ({count / len(texts):.1%})  {opening}")

    classes = Counter(row.get("classe_cible") for row in data)
    print("\nTarget classes:", dict(sorted(classes.items(), key=lambda kv: str(kv[0]))))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name_dataset`` and ``top``.
    """
    parser = argparse.ArgumentParser(description="Diversity statistics of a generated corpus")
    parser.add_argument("name_dataset", type=str)
    parser.add_argument("--top", type=int, default=20)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    report(dataset_path=args.name_dataset, top=args.top)
