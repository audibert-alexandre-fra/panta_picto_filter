import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src" / "panta_picto_filter"))

from model import LlmAsJudge


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a model into cache")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen3-14B",
        help="HuggingFace model identifier (default: Qwen/Qwen3-14B)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Loading {args.model} into cache...")
    model = LlmAsJudge(name_model=args.model, task="filter_text_picto")
    print(f"Model {args.model} loaded and cached.")


if __name__ == "__main__":
    main()
