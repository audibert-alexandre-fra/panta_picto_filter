from seeds import STRUCTURES, PromptSpec


PROMPT_GENERATION = """
Tu écris des phrases en français pour entraîner un système de Communication Alternative
et Augmentative (CAA) : chaque phrase sera traduite en une suite de pictogrammes.

IMPORTANT :
- Réponds uniquement avec un JSON valide de la forme {"phrases": ["...", "..."]}
- Exactement une phrase par consigne, dans l'ordre des consignes
- Aucune explication, aucun texte supplémentaire

Règles pour chaque phrase :
- Français correct, naturel, comme on le dit ou l'écrit dans la vie de tous les jours
- Une seule phrase complète, de 3 à 20 mots, avec sa ponctuation finale (. ? !)
- Vocabulaire concret, que des pictogrammes peuvent représenter
- Respecte la consigne : intention, structure, temps et type de phrase
- Pas de personne célèbre, de marque, de sigle, de chiffre compliqué ni de caractère spécial
- Pas de guillemets ni de discours rapporté
- Les phrases doivent être différentes les unes des autres : varie le sujet
  (je, tu, nous, on, vous, un prénom, un nom commun), le verbe et le début de phrase
- Évite les tournures toutes faites répétées ("Est-ce que je peux…", "J'aimerais…")
- Pour les questions, varie la forme : intonation ("Tu viens ?"), "est-ce que",
  inversion ("Veux-tu du pain ?"), mot interrogatif (où, quand, qui, quoi, pourquoi,
  comment, combien, quel), question fermée (réponse oui/non) ou ouverte
"""


def build_user_message(spec: PromptSpec) -> str:
    """Write the user message listing one constraint per sentence.

    Args:
        spec: Context and sentence specs of the prompt.

    Returns:
        The user message.
    """
    lines = [
        f"Thème : {spec.theme}",
        f"Lieu : {spec.lieu}",
        f"Qui parle : {spec.locuteur}",
        "",
        "Consignes :",
    ]
    for i, sentence in enumerate(spec.sentences, start=1):
        lines.append(
            f"{i}. {sentence.intention} ; {STRUCTURES[sentence.classe_cible]} ; "
            f"temps : {sentence.temps} ; phrase {sentence.type_phrase}"
        )
    return "\n".join(lines)
