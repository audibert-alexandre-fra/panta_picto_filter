import argparse
import os
from datasets import Dataset
from utils import read_json, save_json
from model import LlmAsJudge
from process_output import parse_llm_output


BATCH_SIZE: int = 64
LOG_EVAL_NB: int = 128
ARASAAC_PATH: str = "/home/getalp/audibeal/evaluate_picto/data/arasaac_en.json"
NB_SENSES: int = 3
# Repo-root file, resolved from this script so it works whatever the cwd.
DESCRIPTIONS_PATH: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "descriptions_cleaned.json"
)
MAX_DESCRIPTION_WORDS: int = 25
# Grammatical pictos have abstract images whose descriptions only mislead
# the judge, so their description is not shown.
NO_DESCRIPTION_TOKENS: set[str] = {
    "past", "future", "question", "!", "?", "be", "have", "and", "or", "but",
    "of", "to", "in", "at_the", "for", "with", "by", "from", "that", "this",
    "that_one", "those", "these", "some", "all", "no", "never", "not", "very",
    "more", "less", "plus_sign", "few", "many", "a_lot", "a_lot_of", "one",
    "I", "you", "he", "she", "it", "It", "we", "us", "they", "my", "your",
    "his", "our", "theirs", "there", "there_is", "here", "be_able_to",
    "obligation", "want", "need", "if", "when", "because", "after", "before",
    "during", "until", "again", "now", "above", "under", "where", "how", "why",
    "what", "who", "which?",
}


def load_picto_senses(path: str = ARASAAC_PATH) -> dict[int, str]:
    """Map each ARASAAC picto id to its first keywords joined by ``/``.

    Lets the judge check the actual pictograms, whose alternative senses
    often resolve tokens that look wrong on their own ("teat" → breast).
    Returns an empty dict (judge then sees text/tokens only) if the
    lexicon is missing, so a job never dies on it.
    """
    senses: dict[int, str] = {}
    if not os.path.exists(path):
        print(f"[warning] lexique ARASAAC introuvable ({path}) : filtrage sur text/tokens seulement")
        return senses
    for entry in read_json(path):
        keywords: list[str] = []
        for kw in entry.get("keywords", []):
            word = kw["keyword"].replace(" ", "_")
            if word not in keywords:
                keywords.append(word)
        if keywords:
            senses[entry["_id"]] = "/".join(keywords[:NB_SENSES])
    return senses


def load_picto_descriptions(path: str = DESCRIPTIONS_PATH) -> dict[int, str]:
    """Map each picto id to a short description of its image.

    Lets the judge recognise pictos that are visually close to the source
    concept even when their keyword looks unrelated. Descriptions are cut to
    ``MAX_DESCRIPTION_WORDS`` to keep long sentences within the context
    window. Returns an empty dict if the file is missing.
    """
    if not os.path.exists(path):
        print(f"[warning] descriptions visuelles introuvables ({path}) : filtrage sans descriptions")
        return {}
    return {
        int(picto_id): " ".join(description.split()[:MAX_DESCRIPTION_WORDS])
        for picto_id, description in read_json(path).items()
    }


def build_input(
    single_input: dict,
    senses: dict[int, str],
    descriptions: dict[int, str] | None = None,
) -> str:
    """Format one example for the judge, adding picto senses and visual
    descriptions when available."""
    text = f"Phrase source : \"{single_input['text']}\"\nTokens : {single_input['tokens']}"
    pictos = single_input.get("pictos")
    if not pictos:
        return text
    if descriptions:
        tokens = single_input["tokens"].split()
        lines = []
        for i, picto in enumerate(pictos):
            picto = int(picto)
            token = tokens[i] if i < len(tokens) else str(picto)
            line = f"- {token} ({senses.get(picto, token)})"
            if picto in descriptions and token not in NO_DESCRIPTION_TOKENS:
                line += f" : {descriptions[picto]}"
            lines.append(line)
        text += "\nPictos (sens / image) :\n" + "\n".join(lines)
    elif senses:
        text += "\nPictos : " + " ".join(senses.get(int(p), str(p)) for p in pictos)
    return text


def judge_both(model: LlmAsJudge, texts: list[str]) -> list[tuple[bool, dict, dict]]:
    """Run the tolerant and the strict judge on ``texts``.

    Returns, per text, whether both judges accept it (rejecting too much is
    preferred over letting noisy picto sequences into the training set) and
    their parsed outputs.
    """
    model.task = "filter_text_picto"
    outputs = model.process_texts(texts=texts)
    model.task = "filter_text_picto_strict"
    outputs_strict = model.process_texts(texts=texts)
    verdicts = []
    for output, output_strict in zip(outputs, outputs_strict):
        parsed = parse_llm_output(output)
        parsed_strict = parse_llm_output(output_strict)
        valid = parsed.get("valide", 0) == 1 and parsed_strict.get("valide", 0) == 1
        verdicts.append((valid, parsed, parsed_strict))
    return verdicts


def filter_picto(
    dataset_path: str,
    nb_element: int | None = None,
    eval_mode: bool = False,
    arasaac_path: str = ARASAAC_PATH,
    descriptions_path: str = DESCRIPTIONS_PATH,
) -> None:
    """Run picto-text filtering on a parquet dataset.

    Loads a parquet file, processes it in batches through the LLM judge
    with both the ``"filter_text_picto"`` and ``"filter_text_picto_strict"``
    tasks (an example is kept only if both accept it), and saves results
    as JSON.

    Args:
        dataset_path: Path to the input ``.parquet`` file.
        nb_element: Optional cap on the number of elements to process.
        eval_mode: If True, only process the first ``LOG_EVAL_NB`` elements
            and write the logs (phrase source, lemmes, raisonnement, verdict,
            raw output, parsed result) to a ``.log`` file to evaluate
            different prompts.
        arasaac_path: ARASAAC ``arasaac_en.json`` lexicon used to give the
            judge each picto's alternative senses.
        descriptions_path: JSON mapping picto id to a description of its
            image, so the judge can accept visually close pictos.
    """
    name_dataset = dataset_path if dataset_path.endswith(".parquet") else f"{dataset_path}.parquet"
    data: list[dict] = list(Dataset.from_parquet(name_dataset))

    if nb_element is not None:
        data = data[:nb_element]

    if eval_mode:
        data = data[:LOG_EVAL_NB]

    senses = load_picto_senses(arasaac_path)
    descriptions = load_picto_descriptions(descriptions_path)
    model = LlmAsJudge(name_model="Qwen/Qwen3-32B", task="filter_text_picto")

    nb_element = len(data)
    results: list[dict] = []
    log_lines: list[str] = []

    for i in range(0, nb_element, BATCH_SIZE):
        index_max = min(nb_element, i + BATCH_SIZE)
        batch = data[i:index_max]
        texts = [build_input(single_input, senses) for single_input in batch]
        verdicts = judge_both(model, texts)

        # Second chance for rejected examples: the visual descriptions help
        # recognise close pictos, but shown on every example they make the
        # judges reject far too much, so they are only used to rescue.
        rescue_idx = [j for j, (valid, _, _) in enumerate(verdicts) if not valid] if descriptions else []
        rescue_texts = [build_input(batch[j], senses, descriptions) for j in rescue_idx]
        rescued = dict(zip(rescue_idx, judge_both(model, rescue_texts))) if rescue_texts else {}

        for j, single_input in enumerate(batch):
            valid, parsed, parsed_strict = verdicts[j]
            rescue = rescued.get(j)
            single_input["filter_picto_text"] = int(valid or (rescue is not None and rescue[0]))
            single_input["filter_picto_text_rescued"] = int(not valid and single_input["filter_picto_text"] == 1)
            results.append(single_input)
            if eval_mode:
                verdict = "valide (1)" if single_input["filter_picto_text"] == 1 else "rejeté (0)"
                lines = [
                    f"=== Exemple {len(results)} ===",
                    f"Phrase source : {single_input['text']}",
                    f"Lemmes : {single_input.get('tokens', 'N/A')}",
                    f"Pictos : {single_input.get('pictos', 'N/A')}",
                    f"Entrée juge : {texts[j]}",
                    f"Raisonnement : {parsed.get('reasoning', 'N/A')}",
                    f"Raisonnement strict : {parsed_strict.get('reasoning', 'N/A')}",
                ]
                if rescue is not None:
                    lines += [
                        f"Repêchage (avec descriptions) : {'oui' if rescue[0] else 'non'}",
                        f"Raisonnement repêchage : {rescue[1].get('reasoning', 'N/A')}",
                        f"Raisonnement strict repêchage : {rescue[2].get('reasoning', 'N/A')}",
                    ]
                lines.append(f"Verdict : {verdict}")
                log_lines.append("\n".join(lines))

    nb_valid = sum(r.get("filter_picto_text", 0) for r in results)
    print(f"{nb_valid}/{nb_element} exemples valides")

    # Suffix eval runs so they never overwrite a full run's output.
    suffix = "_eval" if eval_mode else ""
    name_dataset_save = os.path.splitext(os.path.basename(name_dataset))[0] + f"_filtering_text_picto{suffix}.json"
    save_json(path=name_dataset_save, data=results)

    if eval_mode:
        name_log = os.path.splitext(os.path.basename(name_dataset))[0] + "_eval.log"
        with open(name_log, "w", encoding="utf-8") as f:
            f.write("\n\n".join(log_lines) + "\n")
        print(f"[eval mode] {nb_element} exemples loggés dans {name_log}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name_dataset``.
    """
    parser = argparse.ArgumentParser(description="Process dataset with config file")
    parser.add_argument("name_dataset", type=str)
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Mode évaluation : traite uniquement les 128 premiers exemples et écrit les logs dans un fichier .log",
    )
    parser.add_argument(
        "--arasaac",
        type=str,
        default=ARASAAC_PATH,
        help="Chemin du lexique arasaac_en.json (sens alternatifs des pictos)",
    )
    parser.add_argument(
        "--descriptions",
        type=str,
        default=DESCRIPTIONS_PATH,
        help="Chemin du JSON id de picto -> description de son image",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    filter_picto(dataset_path=args.name_dataset, eval_mode=args.eval, arasaac_path=args.arasaac,
                 descriptions_path=args.descriptions)
