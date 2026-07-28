import argparse
import os
from pathlib import Path
from time import time

from datasets import Dataset
from utils import save_json
from model import LlmAsJudge
from process_output import parse_llm_output


BATCH_SIZE: int = 64


def filter_picto(dataset_path: str, nb_element: int | None = None) -> None:
    """Run picto-text filtering on a parquet dataset.

    Loads a parquet file, processes it in batches through the LLM judge
    using the ``"filter_text_picto"`` task, and saves results as JSON.

    Args:
        dataset_path: Path to the input ``.parquet`` file.
        nb_element: Optional cap on the number of elements to process.
    """
    name_dataset = dataset_path if dataset_path.endswith(".parquet") else f"{dataset_path}.parquet"
    data: list[dict] = list(Dataset.from_parquet(name_dataset))

    if nb_element is not None:
        data = data[:nb_element]

    model = LlmAsJudge(name_model="Qwen/Qwen3-14B", task="filter_text_picto")

    nb_element = len(data)
    results: list[dict] = []
    starting_time = time()

    for i in range(0, nb_element, BATCH_SIZE):
        index_max = min(nb_element, i + BATCH_SIZE)
        batch = data[i:index_max]
        texts = [
            f"Phrase source : \"{single_input['text']}\"\nTokens : {single_input['tokens']}"
            for single_input in batch
        ]
        outputs = model.process_texts(texts=texts)
        for output, single_input in zip(outputs, batch):
            parsed = parse_llm_output(output)
            single_input["filter_picto_text"] = parsed.get("valide", 0)
            results.append(single_input)

    nb_filtered = sum(r.get("filter_picto_text", 0) for r in results)

    name_dataset_save = os.path.splitext(os.path.basename(name_dataset))[0] + "_filtering_text_picto.json"
    save_json(path=name_dataset_save, data=results)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name_dataset``.
    """
    parser = argparse.ArgumentParser(description="Process dataset with config file")
    parser.add_argument("name_dataset", type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    filter_picto(dataset_path=args.name_dataset)
