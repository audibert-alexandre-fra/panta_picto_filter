import argparse

from utils import read_json, save_json
from model import LlmAsJudge
from process_output import parse_llm_classification


BATCH_SIZE: int = 64


def classify_dataset(dataset_path: str, nb_element: int | None = None) -> None:
    """Classify French sentences into 6 complexity classes.

    Loads a JSON dataset, processes it in batches through the LLM judge
    using the ``"classification"`` task, and saves results as JSON.

    Args:
        dataset_path: Path to the input ``.json`` file.
        nb_element: Optional cap on the number of elements to process.
    """
    name_dataset = dataset_path if dataset_path.endswith(".json") else f"{dataset_path}.json"
    data: list[dict] = read_json(name_dataset)

    if nb_element is not None:
        data = data[:nb_element]

    model = LlmAsJudge(task="classification")

    nb_element = len(data)
    results: list[dict] = []

    for i in range(0, nb_element, BATCH_SIZE):
        index_max = min(nb_element, i + BATCH_SIZE)
        batch = data[i:index_max]
        texts = [single_input["text"] for single_input in batch]
        outputs = model.process_texts(texts=texts)
        for text, output in zip(texts, outputs):
            parsed = parse_llm_classification(output)
            results.append({
                "text": text,
                "classe": parsed.get("classe", 6),
            })

    name_dataset_save = name_dataset[:-5] + "_class.json"
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
    classify_dataset(dataset_path=args.name_dataset)
