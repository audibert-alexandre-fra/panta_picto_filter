import pandas as pd
import json
from typing import Any


def read_csv_custom(data_path: str, nb_element: int | None = None, extract_columns: str | None = None) -> pd.DataFrame:
    """Read a CSV file with optional row limiting and column extraction.

    Args:
        data_path: Path to the CSV file.
        nb_element: Maximum number of rows to load. None loads all rows.
        extract_columns: Single column name to extract. None loads all columns.

    Returns:
        A pandas DataFrame with the loaded data.
    """
    data = pd.read_csv(data_path)
    if nb_element is not None:
        data = data.iloc[:nb_element]
    if extract_columns is not None:
        data = data[extract_columns]
    return data


def read_json(path: str) -> list[Any]:
    """Read a JSON file and return its content.

    Args:
        path: Path to the JSON file.

    Returns:
        Content of the JSON file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"{path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: list[Any]) -> None:
    """Save data to a JSON file with pretty-printing.

    Args:
        path: Destination file path. '.json' is appended if not present.
        data: Serialisable data to write.
    """
    if not path.endswith(".json"):
        path += ".json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
