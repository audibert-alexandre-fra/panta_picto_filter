import argparse

from utils import read_json, save_json
from model import LlmAsJudge
from process_output import parse_llm_classification


BATCH_SIZE: int = 64


def process_benoit_format(dataset_path: str, nb_element: int | None = None) -> None:
    """Validate sentences using the LLM judge and save annotated results.

    Loads a JSON dataset, processes it in batches through the LLM judge
    (default task), saves the full annotated dataset, then saves a filtered
    version containing only validated entries (``valide == 1``).

    Args:
        dataset_path: Path to the input ``.json`` file.
        nb_element: Optional cap on the number of elements to process.
    """
    name_dataset = dataset_path if dataset_path.endswith(".json") else f"{dataset_path}.json"
    data: list[dict] = read_json(name_dataset)

    if nb_element is not None:
        data = data[:nb_element]

    model = LlmAsJudge()

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
                "valide": parsed.get("valide", 0),
            })

    name_dataset_save = name_dataset[:4] + "_annotated.json"
    save_json(path=name_dataset_save, data=results)

    results_filtered = [entry for entry in results if entry["valide"] == 1]
    name_dataset_filtered = name_dataset[:4] + "_annotated_filtered.json"
    save_json(path=name_dataset_filtered, data=results_filtered)


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
    process_benoit_format(dataset_path=args.name_dataset)
