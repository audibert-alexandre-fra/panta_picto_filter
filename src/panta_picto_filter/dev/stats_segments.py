
from pathlib import Path

from panta_picto_filter.utils import read_json


parent_path = Path(__file__).resolve().parent.parent / "before_annotation"

path_to_data = [ path for path in parent_path.iterdir() ] #if "filtered_class" in str(path)]

data = []
for path in path_to_data:
    data.extend(read_json(path))

dict_class = {i + 1 : 0 for i in range(5)}
for single_data in data:
    if single_data["classe"] in dict_class:
        dict_class[single_data["classe"]] += 1

total = sum(dict_class.values())
for key in dict_class:
    print(f"Key: {key}, Count: {dict_class[key]}, Percentage: {dict_class[key]/total:.2%}")

print("Pourcentage of classe 5 to keep to reach 2.5M exemple: ")

ratio = (2500000 - total)/ dict_class[5]+ 1

print(total - dict_class[5] + dict_class[5]*ratio)
