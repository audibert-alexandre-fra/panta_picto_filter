import argparse

import pandas as pd
from utils import read_json, save_json
from model import LlmAsJudge
from process_output import parse_llm_classification
from time import time


BATCH_SIZE = 64
parser = argparse.ArgumentParser(description="Process dataset with config file")
parser.add_argument(
    "name_dataset",
    type=str,
)
args = parser.parse_args()
name_dataset = args.name_dataset
nb_element_to_treat = None

# Load data
if not name_dataset.endswith('.json'):
    name_dataset += ".json"
data = read_json(name_dataset)


if nb_element_to_treat is not None:
    data = data[:nb_element_to_treat]
model = LlmAsJudge()

nb_element = len(data)
print(f"Nb data to process {nb_element}")

results = []
starting_time = time()

for i in range(0, nb_element, BATCH_SIZE):
    index_max = min(nb_element, i + BATCH_SIZE)
    batch = data[i:index_max]
    texts = [single_input["text"] for single_input in batch]
    outputs = model.process_texts(texts=texts)
    for text, output in zip(texts, outputs):
        parsed = parse_llm_classification(output)
        results.append({
            "text": text,
            "valide": parsed.get("valide", 0)
        })
name_dataset_save = name_dataset[:4] + '_annotated' + ".json"
save_json(
    path=name_dataset_save,
    data=results
)

results_filered = [single_dict for single_dict in results if single_dict["valide"] == 1]
name_dataset_save = name_dataset[:4] + '_annotated_filtered' + ".json"
save_json(
    path=name_dataset_save,
    data=results_filered
)
