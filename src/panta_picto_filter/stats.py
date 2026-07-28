from panta_picto_filter.utils import read_json

names = ["wikihow", "cosmo", "gute",  "viki"]

if not(isinstance(names, list)):
    names = [names]

for name in names:
    print("==================")
    if name.endswith(".json"):
        name = name[:-4]
    print(name)
    name_to_pull = name + ".json"
    name_annoted = name + "_annotated_filtered.json"
    data_1 = read_json(path=name_to_pull)
    print("Name Data", name_to_pull, len(data_1))
    data_2 = read_json(path=name_annoted)
    print("Name Data", name_to_pull, len(data_2))