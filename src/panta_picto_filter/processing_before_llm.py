import argparse
import os
from pathlib import Path
import random

from panta_picto_filter.utils import save_json, read_json


def processing_json_before_llm_annotation(json_path: str, new_dataset_name: str):
    current_path = Path(__file__).resolve().parent
    if "filtered_class" not in json_path:
        raise ValueError(f"Can't process this dataset because filtered_class is not included in the name current name: {json_path}")
    os.makedirs("before_annotation", exist_ok=True)
    path_to_save = current_path / "before_annotation" / new_dataset_name
    data = read_json(json_path)
    ratio_to_keep = 0.22
    print(f" Nb element in the original dataset {len(data)}")
    final_dataset = []
    for single_data in data:
        classe = single_data["classe"]
        if classe < 5:
            final_dataset.append(single_data)
        elif classe == 5:
            if random.random() < ratio_to_keep:
                final_dataset.append(single_data)
    print(f"Nb element in the final dataset {len(final_dataset)}")
    save_json(path=str(path_to_save), data=final_dataset)


def parse_args():
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
