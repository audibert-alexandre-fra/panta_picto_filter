import argparse
import os

from datasets import Dataset
from panta_picto_filter.utils import read_json


def two_consecutif_pictogramme_detected(list_picto: list[str]) -> bool:
    """Check whether a pictogram list contains two consecutive identical tokens.

    Args:
        list_picto: Ordered list of pictogram tokens.

    Returns:
        ``True`` if at least two adjacent tokens are identical or the list
        has fewer than 2 elements, ``False`` otherwise.
    """
    if len(list_picto) < 2:
        return True
    for index in range(len(list_picto) - 1):
        if list_picto[index] == list_picto[index + 1]:
            return True
    return False


def last_filtering(name: str, name_to_save: str) -> None:
    """Apply final filtering and deduplication before saving as parquet.

    Keeps only entries that passed the picto-text filter
    (``filter_picto_text == 1``), have no consecutive duplicate
    pictograms, and are unique by text content.

    Args:
        name: Path to the JSON results file.
        name_to_save: Destination parquet file name (extension appended
            if missing). Saved under ``final_parquet_dataset/``.
    """
    data = read_json(name)
    filtering_results: list[dict] = []
    all_text: set[str] = set()

    for single_data in data:
        if (
            single_data["filter_picto_text"] == 1
            and not two_consecutif_pictogramme_detected(single_data["pictos"])
            and single_data["text"] not in all_text
        ):
            filtering_results.append(single_data)
            all_text.add(single_data["text"])

    dataset = Dataset.from_list(filtering_results)
    if not name_to_save.endswith(".parquet"):
        name_to_save += ".parquet"
    dataset.to_parquet(os.path.join("final_parquet_dataset", name_to_save))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name`` and ``save``.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, help="Name of parquet to Merge")
    parser.add_argument("--save", type=str, help="Name of parquet to Merge")
    return parser.parse_args()


if __name__ == "__main__":
    arg = parse_args()
    last_filtering(name=arg.name, name_to_save=arg.save)
