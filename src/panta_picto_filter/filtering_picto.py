import argparse
import os
from pathlib import Path

import pandas as pd
from utils import read_json, save_json
from model import LlmAsJudge
from process_output import parse_llm_classification, parse_llm_output
from time import time
from datasets import load_dataset, Dataset


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
if not name_dataset.endswith('.parquet'):
    name_dataset += ".parquet"
data = list(Dataset.from_parquet(name_dataset))


if nb_element_to_treat is not None:
    data = data[:nb_element_to_treat]

model = LlmAsJudge(name_model="Qwen/Qwen3-14B",task="filter_text_picto")

nb_element = len(data)
print(f"Nb data to process {nb_element}")

results = []
starting_time = time()

for i in range(0, nb_element, BATCH_SIZE):
    index_max = min(nb_element, i + BATCH_SIZE)
    batch = data[i:index_max]
    texts = [
        f"Phrase source : \"{single_input['text']}\"\nTokens : {single_input['tokens']}"
        for single_input in batch
    ]
    print(texts)
    outputs = model.process_texts(texts=texts)
    for text, output, single_input in zip(texts, outputs, batch):
        print("============================================")
        print(output, text)
        parsed = parse_llm_output(output)
        single_input["filter_picto_text"] = parsed.get("valide", 0)
        results.append(single_input)

# compute ration filtered
nb_filtered = sum(r.get("filter_picto_text", 0) for r in results)
print(f"Nombre d'éléments filtrés : {nb_filtered} sur {nb_element} ({nb_filtered / nb_element:.2%})")
print(f"Temps total de traitement : {time() - starting_time:.2f} secondes, temps moyen par élément : {(time() - starting_time) / nb_element:.2f} secondes")
name_dataset_save = (
    os.path.splitext(os.path.basename(name_dataset))[0]
    + "_filtering_text_picto.json"
)
save_json(
    path=name_dataset_save,
    data=results
)
# dataset = Dataset.from_list(results)
# name_dataset_save = os.path.basename(name_dataset) + '_filtering_text_picto' + ".parquet"
# dataset.to_parquet(os.path.join("final_parquet_dataset", name_dataset_save))
