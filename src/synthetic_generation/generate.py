import argparse
import json
import re
from pathlib import Path

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

from prompt import PROMPT_GENERATION, build_user_message
from seeds import PromptSpec, sample_prompt_specs


DEFAULT_MODEL: str = "Qwen/Qwen3-32B"
# ~450k raw sentences for ~300k after dedup + LLM validation (see clean.sh).
DEFAULT_NB_PROMPTS: int = 45_000
SENTENCES_PER_PROMPT: int = 10
# Prompts sent to vLLM between two checkpoints.
CHUNK_SIZE: int = 2_000
DEFAULT_OUTPUT: str = "../../outputs/synthetic-fr_sentences.json"

# The other corpora are tokenized only at the end of the sentence ("la Gaule .", commas
# glued): reproduce it so pre_clean.py's detokenize() applies unchanged.
FINAL_PUNCT = re.compile(r"\s*([.!?…]+)\s*$")
LEADING_NUMBER = re.compile(r"^\s*\d+[.)]\s*")


def tokenize_final_punct(text: str) -> str:
    """Separate the sentence-final punctuation: "Je veux boire." -> "Je veux boire ."

    The typographic apostrophe the model mixes in ("J’ai") is normalised to "'" like
    in the other corpora, so that dedup and picto annotation see a single form.
    """
    return FINAL_PUNCT.sub(r" \1", text.strip().replace("’", "'"))


def parse_sentences(text: str) -> list[str]:
    """Parse the ``{"phrases": [...]}`` output of the model.

    Like ``process_output.py``, never raises: a malformed output yields no sentence.

    Args:
        text: Raw LLM output.

    Returns:
        The generated sentences, stripped of any leading numbering.
    """
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group())
        except Exception:
            return []

    phrases = data.get("phrases") if isinstance(data, dict) else None
    if not isinstance(phrases, list):
        return []
    sentences = [LEADING_NUMBER.sub("", p).strip() for p in phrases if isinstance(p, str)]
    return [s for s in sentences if s]


def to_rows(spec: PromptSpec, sentences: list[str]) -> list[dict]:
    """Attach each sentence to the spec it answers.

    When the model returned a different number of sentences, the per-sentence specs
    cannot be matched and only the shared context is kept.
    """
    rows = []
    for i, sentence in enumerate(sentences):
        if len(sentences) == len(spec.sentences):
            metadata = spec.metadata(i)
        else:
            metadata = {"theme": spec.theme, "lieu": spec.lieu, "locuteur": spec.locuteur}
        rows.append({"text": tokenize_final_punct(sentence), **metadata})
    return rows


def generate(
    output_path: str,
    nb_prompts: int,
    sentences_per_prompt: int,
    name_model: str,
    temperature: float,
    seed: int,
) -> None:
    """Generate synthetic CAA sentences with vLLM.

    Rows are appended to ``<output>.partial.jsonl`` after each chunk of prompts; a
    rerun with the same arguments resumes after the last finished chunk. The final
    ``[{"text": ..., <metadata>}]`` file is written at the end, ready for clean.sh.

    Args:
        output_path: Destination ``.json`` file.
        nb_prompts: Number of prompts (``sentences_per_prompt`` sentences each).
        sentences_per_prompt: Sentences asked per prompt.
        name_model: Hugging Face model.
        temperature: Sampling temperature (high for diversity).
        seed: Seed of the sampled combinations.
    """
    specs = sample_prompt_specs(nb_prompts, sentences_per_prompt, seed)
    partial_path = Path(output_path).with_suffix(".partial.jsonl")
    done_path = Path(output_path).with_suffix(".partial.done")
    nb_done = int(done_path.read_text()) if done_path.exists() else 0
    if nb_done:
        print(f"Resuming after {nb_done} prompts")

    tokenizer = AutoTokenizer.from_pretrained(name_model)
    llm = LLM(model=name_model, max_model_len=4096, gpu_memory_utilization=0.9)
    sampling_params = SamplingParams(
        temperature=temperature,
        top_p=0.95,
        max_tokens=60 * sentences_per_prompt,
        seed=seed,
    )

    for start in range(nb_done, nb_prompts, CHUNK_SIZE):
        chunk = specs[start:start + CHUNK_SIZE]
        prompts = [
            tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": PROMPT_GENERATION},
                    {"role": "user", "content": build_user_message(spec)},
                ],
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            for spec in chunk
        ]
        outputs = llm.generate(prompts, sampling_params)

        nb_failed = 0
        with open(partial_path, "a", encoding="utf-8") as f:
            for spec, output in zip(chunk, outputs):
                sentences = parse_sentences(output.outputs[0].text)
                nb_failed += not sentences
                for row in to_rows(spec, sentences):
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        done_path.write_text(str(start + len(chunk)))
        print(f"{start + len(chunk)}/{nb_prompts} prompts ({nb_failed} unparsable in this chunk)")

    with open(partial_path, "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4, ensure_ascii=False)
    print(f"{output_path}: {len(rows)} sentences")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic CAA sentences")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT)
    parser.add_argument("--nb_prompts", type=int, default=DEFAULT_NB_PROMPTS)
    parser.add_argument("--sentences_per_prompt", type=int, default=SENTENCES_PER_PROMPT)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate(
        output_path=args.output,
        nb_prompts=args.nb_prompts,
        sentences_per_prompt=args.sentences_per_prompt,
        name_model=args.model,
        temperature=args.temperature,
        seed=args.seed,
    )
