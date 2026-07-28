from typing import Any

from panta_picto_filter.utils import read_json


def load_classification(path: str = "wikihow_annotated_filtered_class.json") -> list[dict[str, Any]]:
    """Load a classification JSON file.

    Args:
        path: Path to the classification JSON file.

    Returns:
        The list of classified entries.
    """
    return read_json(path=path)
