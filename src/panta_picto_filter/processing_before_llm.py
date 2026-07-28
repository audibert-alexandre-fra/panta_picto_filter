import argparse
import os
import random
from pathlib import Path

from panta_picto_filter.utils import save_json, read_json


RATIO_TO_KEEP_CLASS_5: float = 0.22


def processing_json_before_llm_annotation(json_path: str, new_dataset_name: str) -> None:
    """Downsample a classified dataset before LLM annotation.

    Keeps all entries with ``classe < 5`` and randomly samples a fraction
    (``RATIO_TO_KEEP_CLASS_5``) of class-5 entries. The resulting dataset
    is saved under ``before_annotation/``.

    Args:
        json_path: Path to the input ``*_filtered_class.json`` file.
        new_dataset_name: Name of the output file (saved inside
            ``before_annotation/``).

    Raises:
        ValueError: If ``filtered_class`` is not part of *json_path*.
    """
    current_path = Path(__file__).resolve().parent
    if "filtered_class" not in json_path:
        raise ValueError(
            f"Can't process this dataset because filtered_class is not included "
            f"in the name current name: {json_path}"
        )
    os.makedirs("before_annotation", exist_ok=True)
    path_to_save = current_path / "before_annotation" / new_dataset_name
    data = read_json(json_path)

    final_dataset: list[dict] = []
    for single_data in data:
        classe = single_data["classe"]
        if classe < 5:
            final_dataset.append(single_data)
        elif classe == 5:
            if random.random() < RATIO_TO_KEEP_CLASS_5:
                final_dataset.append(single_data)

    save_json(path=str(path_to_save), data=final_dataset)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``json_path`` and ``new_dataset_name``.
    """
    parser = argparse.ArgumentParser(
        description="Process a filtered_class dataset before LLM annotation."
    )
    parser.add_argument(
        "--json_path",
        type=str,
        required=True,
        help="Path to the input JSON dataset.",
    )
    parser.add_argument(
        "--new_dataset_name",
        type=str,
        required=True,
        help="Name of the output dataset file.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    processing_json_before_llm_annotation(
        json_path=args.json_path,
        new_dataset_name=args.new_dataset_name,
    )
