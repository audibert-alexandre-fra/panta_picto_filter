import argparse
import json
import random
from collections import Counter
from pathlib import Path

CHUNK_SIZE = 40_000
KEEP_ALL_CLASSES = (1, 2)
BALANCED_CLASSES = (3, 4, 5)
DROPPED_CLASSES = (6,)
INPUT_DIR = Path(__file__).parent / "filtered_class"
OUTPUT_DIR = Path(__file__).parent / "chunks_balanced_345"


def allocate_quota(available: dict[str, int], quota: int) -> dict[str, int]:
    """Split ``quota`` across sources proportionally to ``available``.

    Uses the largest-remainder method so the shares sum exactly to ``quota``.
    """
    total = sum(available.values())
    exact = {source: quota * n / total for source, n in available.items()}
    shares = {source: int(value) for source, value in exact.items()}
    missing = quota - sum(shares.values())
    by_remainder = sorted(exact, key=lambda s: exact[s] - shares[s], reverse=True)
    for source in by_remainder[:missing]:
        shares[source] += 1
    return shares


def main(input_dir: Path, output_dir: Path, chunk_size: int, seed: int) -> None:
    rng = random.Random(seed)
    output_dir.mkdir(exist_ok=True)

    datasets: dict[str, list[dict]] = {}
    for path in sorted(input_dir.glob("*filtered_class.json")):
        base_name = path.name.replace("filtered_class.json", "").rstrip("_")
        with open(path, "r", encoding="utf-8") as f:
            datasets[base_name] = json.load(f)

    counts = {
        name: Counter(row["classe"] for row in data) for name, data in datasets.items()
    }
    class_totals = {
        c: sum(counts[name][c] for name in datasets) for c in BALANCED_CLASSES
    }
    quota = min(class_totals.values())
    print(f"Totals for classes {BALANCED_CLASSES}: {class_totals} -> quota per class = {quota}")

    shares = {
        c: allocate_quota({name: counts[name][c] for name in datasets}, quota)
        for c in BALANCED_CLASSES
    }

    kept_counts: dict[str, Counter] = {}
    for name, data in datasets.items():
        indices_by_class: dict[int, list[int]] = {}
        for idx, row in enumerate(data):
            indices_by_class.setdefault(row["classe"], []).append(idx)

        kept: list[int] = []
        for c in KEEP_ALL_CLASSES:
            kept += indices_by_class.get(c, [])
        for c in BALANCED_CLASSES:
            kept += rng.sample(indices_by_class.get(c, []), shares[c][name])
        kept.sort()  # keep the original sentence order (context for coreference)

        selected = [data[i] for i in kept]
        kept_counts[name] = Counter(row["classe"] for row in selected)
        print(f"{name}: {len(data)} -> {len(selected)} sentences")

        for i in range(0, len(selected), chunk_size):
            chunk_name = f"{name}_chunk_{i // chunk_size}.json"
            with open(output_dir / chunk_name, "w", encoding="utf-8") as f:
                json.dump(selected[i : i + chunk_size], f, ensure_ascii=False)

    classes = (*KEEP_ALL_CLASSES, *BALANCED_CLASSES)
    total = Counter()
    for c in kept_counts.values():
        total.update(c)
    print(f"Final: {sum(total.values())} sentences, per class: "
          f"{ {c: total[c] for c in classes} } (classes {DROPPED_CLASSES} dropped)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Keep classes 1-2 whole, balance classes 3-4-5 to the same size, drop class 6."
    )
    parser.add_argument("--input_dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--output_dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--chunk_size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.input_dir, args.output_dir, args.chunk_size, args.seed)
