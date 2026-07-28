import json
import re

def parse_llm_output(text: str):
    """
    Parse robuste + sortie simplifiée avec valide binaire
    """
    # 1. extraction JSON robuste
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print(f"[PARSING ERROR] Format de sortie invalide, JSON introuvable dans : {repr(text)}")
            return {"valide": 0}
        try:
            data = json.loads(match.group())
        except Exception:
            print(f"[PARSING ERROR] JSON malformé après extraction : {repr(match.group())}")
            return {"valide": 0}

    # 2. vérification que le champ attendu est présent
    if "valide" not in data:
        print(f"[PARSING ERROR] Champ 'valide' manquant dans le JSON : {data}")
        return {"valide": 0}

    # 3. extraction sécurisée
    try:
        valide = int(data.get("valide", 0))
    except Exception:
        print(f"[PARSING ERROR] Valeur de 'valide' non convertible en int : {repr(data.get('valide'))}")
        valide = 0

    return {"valide": valide}


def parse_llm_classification(text: str):
    """
    Parse robuste + sortie simplifiée avec classe 5 class
    """
    # 1. extraction JSON robuste
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print(f"[PARSING ERROR] Format de sortie invalide, JSON introuvable dans : {repr(text)}")
            return {"classe": 6}
        try:
            data = json.loads(match.group())
        except Exception:
            print(f"[PARSING ERROR] JSON malformé après extraction : {repr(match.group())}")
            return {"classe": 6}

    # 2. vérification que le champ attendu est présent
    if "classe" not in data:
        print(f"[PARSING ERROR] Champ 'valide' manquant dans le JSON : {data}")
        return {"classe": 6}

    # 3. extraction sécurisée
    try:
        classe = int(data.get("classe", 6))
    except Exception:
        print(f"[PARSING ERROR] Valeur de 'classe' non convertible en int : {repr(data.get('classe'))}")
        classe = 6

    if classe > 6 or classe < 1:
        print(f' error class {classe}')
        classe = 6

    return {"classe": classe}