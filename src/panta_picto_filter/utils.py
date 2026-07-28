import pandas as pd
import json
from typing import Any
from pathlib import Path


def read_csv_custom(data_path: str, nb_element: int|None=None, extract_columns: str|None=None) -> pd.DataFrame:
    data = pd.read_csv(data_path)
    if nb_element is not None:
        data = data.iloc[:nb_element]
    if extract_columns is not None:
        data = data[extract_columns]
    return data


def read_json(path: str) -> dict[str, Any]:
    """
    Read a JSON file and return its content.
    
    Args:
        path: Path to the JSON file
        
    Returns:
        Content of the JSON file
    """
    if not Path(path).exists():
        raise FileNotFoundError(f"{path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: str, data: dict[str, Any]):
    if not(path.endswith(".json")):
        path += ".json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


if __name__ == '__main__':
    print(read_csv_custom("corpus_phrase.csv",  nb_element=1000))