import argparse
import os
from datasets import load_dataset, Dataset
from panta_picto_filter.utils import read_json


def two_consecutif_pictogramme_detected(list_picto) -> bool:
    if len(list_picto) < 2:
        return True
    for index in range(len(list_picto) - 1):
        if list_picto[index] == list_picto[index+1]:
            return True
    return False


def last_fitlering(name: str, name_to_save: str) -> None:
    data = read_json(name)
    filtering_results = []
    print(f' Nb data {len(data)}, in dataset {name}')
    # Remove doublons
    all_text = set()
    for single_data in data:
        if single_data["filter_picto_text"] == 1 and not two_consecutif_pictogramme_detected(single_data["pictos"]):
            if single_data["text"] not in all_text:
                filtering_results.append(single_data)
                all_text.add(single_data["text"])
                
    print(f'End {len(filtering_results)}, in dataset {name}')
    dataset = Dataset.from_list(filtering_results)
    if not(name_to_save.endswith(".parquet")):
        name_to_save += ".parquet"
    dataset.to_parquet(os.path.join("final_parquet_dataset", name_to_save))


def set_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        type=str,
        help="Name of parquet to Merge"
    )
    parser.add_argument(
        "--save",
        type=str,
        help="Name of parquet to Merge"
    )
    return parser.parse_args()


if __name__ == '__main__':
    arg = set_argparse()
    last_fitlering(name=arg.name, name_to_save=arg.save)