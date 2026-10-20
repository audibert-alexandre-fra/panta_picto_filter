import argparse
from pathlib import Path

from utils import read_json, save_json
from model import LlmAsJudge
from process_output import parse_llm_output
from pre_clean import MAX_WORDS


BATCH_SIZE: int = 64
DEFAULT_MODEL: str = "Qwen/Qwen3-32B"


def process_benoit_format(
    dataset_path: str,
    nb_element: int | None = None,
    name_model: str = DEFAULT_MODEL,
) -> None:
    """Validate sentences using the LLM judge and save annotated results.

    Loads a JSON dataset, processes it in batches through the LLM judge
    (default task), saves the full annotated dataset, then saves a filtered
    version containing only validated entries (``valide == 1``). Sentences
    longer than ``MAX_WORDS`` words are dropped before the LLM call.

    Args:
        dataset_path: Path to the input ``.json`` file.
        nb_element: Optional cap on the number of elements to process.
        name_model: Hugging Face model used as judge.
    """
    name_dataset = dataset_path if dataset_path.endswith(".json") else f"{dataset_path}.json"
    data: list[dict] = read_json(name_dataset)

    if nb_element is not None:
        data = data[:nb_element]

    nb_before = len(data)
    data = [entry for entry in data if len(entry["text"].split()) <= MAX_WORDS]
    print(f"Dropped {nb_before - len(data)} sentences longer than {MAX_WORDS} words")

    model = LlmAsJudge(name_model=name_model, task="filter_text")

    nb_element = len(data)
    results: list[dict] = []

    for i in range(0, nb_element, BATCH_SIZE):
        index_max = min(nb_element, i + BATCH_SIZE)
        batch = data[i:index_max]
        texts = [single_input["text"] for single_input in batch]
        outputs = model.process_texts(texts=texts)
        for text, output in zip(texts, outputs):
            parsed = parse_llm_output(output)
            results.append({
                "text": text,
                "valide": parsed.get("valide", 0),
            })

    input_path = Path(name_dataset)
    name_dataset_save = str(input_path.with_name(f"{input_path.stem}_annotated.json"))
    save_json(path=name_dataset_save, data=results)

    results_filtered = [entry for entry in results if entry["valide"] == 1]
    name_dataset_filtered = str(input_path.with_name(f"{input_path.stem}_annotated_filtered.json"))
    save_json(path=name_dataset_filtered, data=results_filtered)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name_dataset``, ``model`` and ``nb_element``.
    """
    parser = argparse.ArgumentParser(description="Process dataset with config file")
    parser.add_argument("name_dataset", type=str)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--nb_element", type=int, default=None, help="Only process the first N sentences (quick test)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    process_benoit_format(
        dataset_path=args.name_dataset,
        nb_element=args.nb_element,
        name_model=args.model,
    )
