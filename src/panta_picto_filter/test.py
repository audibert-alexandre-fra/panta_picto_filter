import pandas as pd
from utils import read_csv_custom
from model import LlmAsJudge
from process_output import parse_llm_output

BATCH_SIZE = 64

# Load data
data = read_csv_custom("corpus_phrase.csv", nb_element=1000)

model = LlmAsJudge()

nb_element = len(data)
print(f"Nb data to process {nb_element}")

results = []

for i in range(0, nb_element, BATCH_SIZE):
    index_max = min(nb_element, i + BATCH_SIZE)
    batch = data.iloc[i:index_max]
    sentences = batch["sentence"].tolist()
    gutenberg_ids = batch["gutenberg_id"].tolist()
    outputs = model.process_texts(texts=sentences)
    for sent, gid, output in zip(sentences, gutenberg_ids, outputs):
        parsed = parse_llm_output(output)
        to_keep = parsed.get("score", 0)
        pertinence_pictogramme = parsed.get("pertinence_pictogramme", 0)
        results.append({
            "gutenberg_id": gid,
            "text": sent,
            "to_keep": to_keep,
            "pertinence_pictogramme": pertinence_pictogramme
        })

# Create final dataframe
df_out = pd.DataFrame(results)

# Save annotation CSV
df_out.to_csv("corpus_phrase_annotated.csv", index=False)
print("Done -> corpus_phrase_annotated.csv generated")

df_filterd = df_out[df_out["to_keep"] == 1]

df_filterd = df_filterd.sort_values(
    by="pertinence_pictogramme",
    ascending=False
)
df_filterd.to_csv("corpus_phrase_filtered.csv", index=False)
