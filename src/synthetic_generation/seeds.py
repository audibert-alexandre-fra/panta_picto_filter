import random
from dataclasses import asdict, dataclass


# Each prompt fixes a context (theme, place, speaker) and asks for one sentence per
# sentence spec (intention, structure, tense, sentence type): the combinations are
# what keeps 300k sentences from collapsing into the same few templates.

THEMES: list[str] = [
    "les repas et la cuisine", "les boissons", "le petit-déjeuner", "les courses au magasin",
    "l'hygiène et la toilette", "s'habiller", "le sommeil et la fatigue", "la santé et la douleur",
    "le médecin et les soins", "les médicaments", "le corps", "les émotions",
    "la famille", "les amis", "les animaux domestiques", "les animaux sauvages",
    "l'école et la classe", "les devoirs", "la récréation", "le travail",
    "les transports", "le bus et le train", "la voiture", "le vélo",
    "la météo", "les saisons", "les vacances", "la plage et la mer",
    "la montagne", "la campagne et la ferme", "la ville", "le jardin",
    "les jeux et jouets", "le sport", "la musique", "la télévision et les films",
    "les livres et les histoires", "le dessin et la peinture", "les fêtes et anniversaires", "Noël",
    "les voisins", "le téléphone et les écrans", "l'argent et les achats", "la maison et le ménage",
    "le rangement", "la cuisine d'un plat précis", "les fruits et légumes", "les couleurs et les formes",
    "le temps qui passe et l'heure", "les sorties au parc", "le restaurant", "le cinéma",
    "la piscine", "le coiffeur", "la pharmacie", "la poste",
    "les règles et les interdits", "les besoins urgents", "les préférences et les goûts", "les souvenirs",
]

PLACES: list[str] = [
    "à la maison", "dans la cuisine", "dans la chambre", "dans la salle de bain", "dans le salon",
    "à l'école", "dans la cour", "au travail", "à l'hôpital", "chez le médecin",
    "au supermarché", "à la boulangerie", "au parc", "dans la rue", "dans le bus",
    "dans la voiture", "à la gare", "à la plage", "à la montagne", "à la campagne",
    "chez les grands-parents", "chez un ami", "au restaurant", "à la piscine", "au centre de loisirs",
]

SPEAKERS: list[str] = [
    "un enfant de 6 ans", "un enfant de 10 ans", "un adolescent", "un adulte",
    "une personne âgée", "une personne qui communique avec des pictogrammes",
    "un parent qui parle à son enfant", "un éducateur ou un soignant",
]

INTENTIONS: list[str] = [
    "exprimer un besoin", "faire une demande polie", "refuser quelque chose", "accepter une proposition",
    "exprimer une émotion", "exprimer une douleur ou un malaise", "poser une question",
    "décrire ce qu'on voit", "raconter un événement", "donner une information",
    "donner un ordre ou une consigne", "exprimer une préférence", "proposer une activité",
    "remercier ou s'excuser", "faire un projet", "se plaindre",
]

# Targets the 1-5 complexity classes of PROMPT_CLASSIFICATION (panta_picto_filter/prompt.py).
STRUCTURES: dict[int, str] = {
    1: "phrase simple (une seule proposition), sans pronom il/elle/le/la/ça renvoyant à "
       "quelque chose, sans prénom ni nom de lieu",
    2: "phrase avec deux propositions (subordonnée ou coordonnée), sans pronom renvoyant à "
       "quelque chose, sans prénom ni nom de lieu",
    3: "phrase contenant un pronom (il, elle, le, la, lui, en, y, ça…) qui renvoie à quelque "
       "chose ou à quelqu'un, sans prénom ni nom de lieu",
    4: "phrase contenant un prénom courant ou un lieu connu (Paris, la mer, la France…), "
       "sans pronom renvoyant à quelque chose",
    5: "phrase contenant un prénom courant et un pronom qui renvoie à une personne ou à une chose",
}
# Real corpora are dominated by class 5 (downsampled in processing_before_llm.py):
# the synthetic set favours the simple classes.
STRUCTURE_WEIGHTS: dict[int, float] = {1: 0.30, 2: 0.25, 3: 0.20, 4: 0.15, 5: 0.10}

TENSE_WEIGHTS: dict[str, float] = {
    "présent": 0.30, "passé composé": 0.15, "futur proche": 0.12, "futur simple": 0.08,
    "imparfait": 0.08, "impératif": 0.15, "conditionnel": 0.12,
}

# Questions are central in CAA: as frequent as affirmative sentences (~34% of the
# sentences once the imperative/question constraints of sample_sentence_spec apply).
SENTENCE_TYPE_WEIGHTS: dict[str, float] = {
    "affirmative": 0.35, "interrogative": 0.35, "négative": 0.15, "exclamative": 0.15,
}


@dataclass
class SentenceSpec:
    """Constraints for one sentence to generate."""

    intention: str
    classe_cible: int
    temps: str
    type_phrase: str


@dataclass
class PromptSpec:
    """Shared context of one prompt and the specs of its sentences."""

    theme: str
    lieu: str
    locuteur: str
    sentences: list[SentenceSpec]

    def metadata(self, index: int) -> dict:
        """Metadata of the ``index``-th sentence, saved next to its text."""
        sentence = asdict(self.sentences[index])
        return {"theme": self.theme, "lieu": self.lieu, "locuteur": self.locuteur, **sentence}


def weighted_choice(rng: random.Random, weights: dict[str, float], exclude: str | None = None) -> str:
    """Draw a key of ``weights`` proportionally to its weight, ``exclude`` left out."""
    keys = [key for key in weights if key != exclude]
    return rng.choices(keys, [weights[key] for key in keys])[0]


def sample_sentence_spec(rng: random.Random, classes: list[int], weights: list[float]) -> SentenceSpec:
    """Sample one sentence spec, without contradictory constraints.

    A question is always interrogative, and an imperative is never interrogative
    ("poser une question ; phrase affirmative" would yield an unnatural sentence).
    """
    intention = rng.choice(INTENTIONS)
    temps = weighted_choice(rng, TENSE_WEIGHTS)
    if intention == "poser une question":
        type_phrase = "interrogative"
        temps = weighted_choice(rng, TENSE_WEIGHTS, exclude="impératif")
    elif temps == "impératif":
        type_phrase = weighted_choice(rng, SENTENCE_TYPE_WEIGHTS, exclude="interrogative")
    else:
        type_phrase = weighted_choice(rng, SENTENCE_TYPE_WEIGHTS)
    return SentenceSpec(
        intention=intention,
        classe_cible=rng.choices(classes, weights)[0],
        temps=temps,
        type_phrase=type_phrase,
    )


def sample_prompt_specs(nb_prompts: int, sentences_per_prompt: int, seed: int) -> list[PromptSpec]:
    """Sample the combinations, deterministically from ``seed``.

    Determinism lets a crashed run resume: the ``i``-th prompt is always the same.

    Args:
        nb_prompts: Number of prompts.
        sentences_per_prompt: Sentences asked per prompt.
        seed: Random seed.

    Returns:
        One ``PromptSpec`` per prompt.
    """
    rng = random.Random(seed)
    classes = list(STRUCTURE_WEIGHTS)
    weights = list(STRUCTURE_WEIGHTS.values())
    specs: list[PromptSpec] = []
    for _ in range(nb_prompts):
        sentences = [
            sample_sentence_spec(rng, classes, weights) for _ in range(sentences_per_prompt)
        ]
        specs.append(PromptSpec(
            theme=rng.choice(THEMES),
            lieu=rng.choice(PLACES),
            locuteur=rng.choice(SPEAKERS),
            sentences=sentences,
        ))
    return specs
