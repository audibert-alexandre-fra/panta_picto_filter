import argparse

from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a model into cache via HuggingFace/transformers")
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen3-32B",
        help="HuggingFace model identifier (default: Qwen/Qwen3-32B)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device to load the model on (default: cuda)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Loading tokenizer for {args.model}...")
    AutoTokenizer.from_pretrained(args.model)
    print(f"Loading model {args.model}...")
    AutoModelForCausalLM.from_pretrained(args.model, device_map=args.device)
    print(f"Model {args.model} loaded and cached.")


if __name__ == "__main__":
    main()
