import json
import re
from typing import Any


def parse_llm_output(text: str) -> dict[str, int]:
    """Parse LLM output for binary validation (valide 0/1).

    Attempts direct JSON parsing, then falls back to regex extraction
    of the first JSON object found in the text.

    Args:
        text: Raw LLM output string.

    Returns:
        A dict with key ``"valide"`` set to 0 or 1.
    """
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {"valide": 0}
        try:
            data = json.loads(match.group())
        except Exception:
            return {"valide": 0}

    if "valide" not in data:
        return {"valide": 0}

    try:
        valide = int(data.get("valide", 0))
    except Exception:
        valide = 0

    return {"valide": valide}


def parse_llm_classification(text: str) -> dict[str, int]:
    """Parse LLM output for 6-class classification.

    Attempts direct JSON parsing, then falls back to regex extraction
    of the first JSON object found in the text.

    Args:
        text: Raw LLM output string.

    Returns:
        A dict with key ``"classe"`` set to an integer between 1 and 6.
    """
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {"classe": 6}
        try:
            data = json.loads(match.group())
        except Exception:
            return {"classe": 6}

    if "classe" not in data:
        return {"classe": 6}

    try:
        classe = int(data.get("classe", 6))
    except Exception:
        classe = 6

    if classe > 6 or classe < 1:
        classe = 6

    return {"classe": classe}
