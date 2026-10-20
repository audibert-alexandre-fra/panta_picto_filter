import argparse
import re
from collections import Counter
from pathlib import Path

from utils import read_json, save_json


# Text saved as cp1252 but decoded as cp1250 (most of Gutenberg): "ŕ la crčme".
MOJIBAKE_CP1250: dict[str, str] = {
    "ŕ": "à", "Ŕ": "À", "č": "è", "Č": "È", "ę": "ê", "Ę": "Ê",
    "ů": "ù", "Ů": "Ù", "ű": "û", "Ű": "Û", "ď": "ï", "Ď": "Ï",
}
# Markers that never occur in French and signal the cp1250 corruption.
MOJIBAKE_CP1250_MARKERS: str = "ŕŔęĘůŮűŰďĎ"

# Second, book-specific corruption found in Gutenberg: "une poupÕe bouclÕe", "Á condition".
MOJIBAKE_BOOK: dict[str, str] = {
    "Õ": "é", "õ": "ê", "Á": "à", "Ò": "è", "ã": "â", "Ó": "ç", "ú": "Ç", "¶": "ô",
    "¨": "«", "£": "»",
}
MOJIBAKE_BOOK_DETECT = re.compile(r"[ÕõÒÓ¶]|\bÁ\b|\wã")
MOJIBAKE_BOOK_U_CIRC = re.compile(r"(?<=\w)«(?=\w)")  # "go«ter" -> "goûter"

INVISIBLE_SPACES = re.compile(r"[\u00a0\u202f\u2009\u2007]")
INVISIBLE_DROP = re.compile(r"[\u200b\u00ad\ufeff]")
MULTI_SPACE = re.compile(r" {2,}")
# Longer "sentences" are merged lists/infoboxes (up to 2 482 words in Vikidia) and
# can overflow the LLM context window.
MAX_WORDS: int = 60

# Markdown bold label at the start: "**Appareils médicaux**: ..." or "** Suffixe:** ...".
# The opening "**" is sometimes lost by sentence splitting: "Marchés de puces:** ...".
BOLD_LABEL = re.compile(r"^\s*(?:\*\*)?\s*[^*:,]{1,60}?\s*(?::\s*\*\*|\*{1,2}\s*:)\s*")
BOLD = re.compile(r"\*\*\s*([^*\n]+?)\s*\*\*")

# Course-structure headings are followed by a title glued to the next sentence
# ("Section 2: Techniques de mélange Une fois les ingrédients..."): reject them.
STRUCTURE_HEADING = re.compile(
    r"^\s*(?:unité de cours|module|section|chapitre|leçon|étape|partie|exercice)\b[^:]{0,12}:",
    re.IGNORECASE,
)
# Title-like labels at the start whose sentence can be kept: "Exemple: ...", "Mythes: ...".
KNOWN_LABEL = re.compile(
    r"^\s*(?:exemples?|conclusion|introduction|remarque|note|astuce|conseil|définition|résumé)"
    r"\s*:\s*",
    re.IGNORECASE,
)
SINGLE_WORD_LABEL = re.compile(r"^\s*([A-ZÀ-Ý][\wÀ-ÿ'’-]{1,24})\s?:\s+(?=\S)")
# Single words that open a real sentence before a colon ("Il dit: ...") - never stripped.
NOT_A_LABEL: set[str] = {
    "il", "elle", "ils", "elles", "on", "je", "j'ai", "tu", "nous", "vous", "ce", "c'est",
    "cela", "ça", "voici", "voilà", "mais", "et", "ou", "donc", "or", "car", "puis",
}

# Sentences cut by the splitter: "Il doit son nom à des taches, appelées « ocelles ."
# or "…à l'exception des reprises de Je t'aime …".
TRAILING_ELLIPSIS = re.compile(r"(?:…|\.\.\.)\s*\.?\s*$")

# Corpora are tokenized ("Il fut nommé d'après la Gaule ."). French typography keeps
# the space before ! ? : ; and around « », so only these are glued back.
SPACE_BEFORE_PUNCT = re.compile(r" +([.,…)\]])")
SPACE_AFTER_OPEN = re.compile(r"([(\[]) +")


def fix_encoding(text: str, fix_cp1250: bool) -> str:
    """Repair the mojibake families observed in the corpora.

    Args:
        text: Sentence to repair.
        fix_cp1250: Whether the corpus is affected by the cp1250 corruption.
            ``č`` alone is ambiguous (Czech names), so this is decided at corpus level.

    Returns:
        The repaired sentence.
    """
    if fix_cp1250:
        text = text.translate(str.maketrans(MOJIBAKE_CP1250))
    if MOJIBAKE_BOOK_DETECT.search(text):
        text = MOJIBAKE_BOOK_U_CIRC.sub("û", text)
        text = text.translate(str.maketrans(MOJIBAKE_BOOK))
    return text


def strip_label(text: str) -> str:
    """Remove a heading-like ``Label:`` prefix, keeping the sentence after it."""
    match = KNOWN_LABEL.match(text)
    if match:
        return text[match.end():]
    match = SINGLE_WORD_LABEL.match(text)
    if match and match.group(1).lower() not in NOT_A_LABEL:
        return text[match.end():]
    return text


def truncation_reason(text: str) -> str | None:
    """Detect a sentence truncated by the sentence splitter.

    Returns:
        The name of the rule that fired, or ``None`` if the sentence looks complete.
    """
    if text.count("«") != text.count("»") or text.count('"') % 2:
        return "unclosed_quote"
    if text.count(")") > text.count("("):  # often a removed pronunciation: "Bruno Nicolè ) est ..."
        return "orphan_paren"
    if text.count("(") > text.count(")"):
        return "unclosed_paren"
    if TRAILING_ELLIPSIS.search(text):
        return "trailing_ellipsis"
    return None


def detokenize(text: str) -> str:
    """Glue tokenized punctuation back: "la Gaule ." -> "la Gaule."."""
    return SPACE_AFTER_OPEN.sub(r"\1", SPACE_BEFORE_PUNCT.sub(r"\1", text))


def clean_sentence(text: str, fix_cp1250: bool) -> tuple[str | None, str]:
    """Clean one sentence with deterministic rules.

    Args:
        text: Raw sentence.
        fix_cp1250: Whether to apply the cp1250 mojibake repair.

    Returns:
        ``(cleaned_text, reason)``. ``cleaned_text`` is ``None`` when the sentence
        is rejected, and ``reason`` names the rule that rejected or modified it
        (``"kept"`` when unchanged).
    """
    original = text
    if "\n" in text:
        return None, "newline"

    text = INVISIBLE_DROP.sub("", INVISIBLE_SPACES.sub(" ", text))
    text = fix_encoding(text, fix_cp1250)

    if STRUCTURE_HEADING.match(text.lstrip("* ")):
        return None, "structure_heading"

    text = BOLD_LABEL.sub("", text)
    text = BOLD.sub(r"\1", text)
    if "*" in text:  # lists, censored words, unbalanced markdown
        return None, "asterisk"

    unlabeled = strip_label(text).lstrip()
    if unlabeled != text.lstrip() and unlabeled[:1].islower():
        unlabeled = unlabeled[0].upper() + unlabeled[1:]
    text = MULTI_SPACE.sub(" ", unlabeled).strip()

    if len(text.split()) > MAX_WORDS:
        return None, "too_long"
    if not text or text.endswith(":") or not re.search(r"[A-Za-zÀ-ÿ]{2}", text):
        return None, "empty_or_heading"
    truncated = truncation_reason(text)
    if truncated is not None:
        return None, truncated

    return text, "kept" if text == original.strip() else "modified"


def corpus_has_cp1250_mojibake(texts: list[str], threshold: float = 0.001) -> bool:
    """Detect whether a corpus is affected by the cp1250 corruption."""
    affected = sum(any(ch in t for ch in MOJIBAKE_CP1250_MARKERS) for t in texts)
    return affected / max(len(texts), 1) > threshold


def pre_clean(dataset_path: str, fix_cp1250: bool | None = None) -> None:
    """Clean a sentence corpus before the LLM judge.

    Writes ``<name>_clean.json`` (sentences to send to the LLM, with the tokenized
    ``text`` and a detokenized ``text_detok``) and
    ``<name>_clean_rejected.json`` (rejected sentences with the rule that fired).

    Args:
        dataset_path: Path to the input ``.json`` file (list of ``{"text": ...}``).
        fix_cp1250: Force the cp1250 repair on/off. ``None`` auto-detects it.
    """
    name_dataset = dataset_path if dataset_path.endswith(".json") else f"{dataset_path}.json"
    data: list[dict] = read_json(name_dataset)
    texts = [entry["text"] for entry in data]

    if fix_cp1250 is None:
        fix_cp1250 = corpus_has_cp1250_mojibake(texts)

    kept: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    reasons: Counter = Counter()
    for text in texts:
        cleaned, reason = clean_sentence(text, fix_cp1250)
        if cleaned is not None and cleaned in seen:
            cleaned, reason = None, "duplicate"
        reasons[reason] += 1
        if cleaned is None:
            rejected.append({"text": text, "reason": reason})
        else:
            seen.add(cleaned)
            # "text" stays tokenized for the picto annotation step.
            kept.append({"text": cleaned, "text_detok": detokenize(cleaned)})

    input_path = Path(name_dataset)
    save_json(path=str(input_path.with_name(f"{input_path.stem}_clean.json")), data=kept)
    save_json(path=str(input_path.with_name(f"{input_path.stem}_clean_rejected.json")), data=rejected)

    print(f"{input_path.name}: {len(texts)} -> {len(kept)} (cp1250 fix: {fix_cp1250})")
    for reason, count in reasons.most_common():
        print(f"  {reason:<18} {count:>9} ({count / len(texts):.1%})")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments with ``name_dataset`` and ``fix_cp1250``.
    """
    parser = argparse.ArgumentParser(description="Rule-based cleaning before the LLM judge")
    parser.add_argument("name_dataset", type=str)
    parser.add_argument(
        "--fix_cp1250",
        choices=["auto", "yes", "no"],
        default="auto",
        help="Repair 'ŕ la crčme'-style mojibake (auto: detect per corpus)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pre_clean(
        dataset_path=args.name_dataset,
        fix_cp1250={"auto": None, "yes": True, "no": False}[args.fix_cp1250],
    )
