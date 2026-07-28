from typing import Union

from panta_picto_filter.utils import read_json


def load_dataset_stats(names: Union[str, list[str]]) -> None:
    """Load and display size information for raw and annotated datasets.

    For each name in *names*, loads ``<name>.json`` and
    ``<name>_annotated_filtered.json`` and prints their lengths.

    Args:
        names: A single dataset name or a list of dataset names
            (without ``.json`` extension).
    """
    if not isinstance(names, list):
        names = [names]

    for name in names:
        if name.endswith(".json"):
            name = name[:-4]
        name_to_pull = f"{name}.json"
        name_annoted = f"{name}_annotated_filtered.json"
        data_raw = read_json(path=name_to_pull)
        data_annotated = read_json(path=name_annoted)


if __name__ == "__main__":
    load_dataset_stats(["wikihow", "cosmo", "gute", "viki"])
