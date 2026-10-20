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
    "les toilettes", "le bain et la douche", "les dents et le dentiste", "les lunettes et les yeux",
    "le fauteuil roulant", "le kinésithérapeute", "l'orthophoniste", "l'hôpital",
    "les allergies", "le rhume et la fièvre", "les blessures et les bobos", "le chaud et le froid",
    "les bébés", "les grands-parents", "les frères et sœurs", "les disputes et la réconciliation",
    "l'amitié et les secrets", "la peur et le noir", "la colère", "la tristesse et le réconfort",
    "la joie et les surprises", "l'ennui", "le bruit et le calme", "la politesse",
    "la cantine", "la bibliothèque", "le goûter", "les desserts et les gâteaux",
    "les légumes à la cantine", "le pique-nique", "la boulangerie", "le marché",
    "l'avion et l'aéroport", "le taxi", "la marche et la promenade", "le camping",
    "la forêt", "la neige et l'hiver", "la pluie et l'orage", "le soleil et l'été",
    "les insectes", "les oiseaux", "les poissons et l'aquarium", "le zoo",
    "les chevaux et le poney", "le football", "la danse", "la natation",
    "les jeux vidéo", "les puzzles et les jeux de société", "les dessins animés", "les chansons",
    "la pâte à modeler et le bricolage", "les déguisements", "le cirque", "le spectacle et le théâtre",
    "les vêtements et les chaussures", "la lessive", "la vaisselle", "les courses de la semaine",
    "les clés et les portes", "les meubles", "la lumière et l'électricité", "les réparations",
    "le facteur et le courrier", "les pompiers", "la police", "les dangers et la sécurité",
    "la route et les feux", "les rendez-vous", "le calendrier et les jours", "le week-end",
    "le matin et le réveil", "le soir et le coucher", "la sieste", "les cauchemars et les rêves",
    "les cadeaux", "les invités", "le mariage", "les photos",
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

# Targets the 1-5 complexity classes of PROMPT_CLASSIFICATION (panta_picto_filter/prompt.py):
# je/tu/nous are not coreference, common nouns ("la mer", "maman") are not named entities.
# Classes 4 and 5 get an imposed named place {entite}: left free, the model takes "la ferme"
# or "la mer" for named entities. No first names: they are not wanted in the corpus.
STRUCTURES: dict[int, str] = {
    1: "phrase simple (une seule proposition), sans pronom il/elle/le/la/ça qui renvoie à "
       "quelque chose, sans prénom ni nom de ville ou de pays",
    2: "phrase avec deux propositions (subordonnée ou coordonnée), sans pronom il/elle/le/la/ça "
       "qui renvoie à quelque chose, sans prénom ni nom de ville ou de pays",
    3: "phrase contenant un pronom (il, elle, le, la, lui, en, y, ça…) qui renvoie à quelque "
       "chose ou à quelqu'un, sans prénom ni nom de ville ou de pays",
    4: "phrase contenant « {entite} », sans pronom il/elle/le/la/ça qui renvoie à quelque chose",
    5: "phrase contenant « {entite} » et un pronom (il, elle, lui, le, la, en, y…) qui renvoie "
       "à ce lieu ou à une chose de la phrase",
}

# Named places with an obvious pictogram, accepted by the validation PROMPT.
NAMED_PLACES: list[str] = [
    "Paris", "Lyon", "Marseille", "Lille", "Bordeaux", "Toulouse", "Nice", "Strasbourg",
    "Nantes", "Montpellier", "Rennes", "Grenoble", "Brest", "Biarritz", "Annecy", "Avignon",
    "Londres", "Rome", "Venise", "Madrid", "Barcelone", "Bruxelles", "Genève", "Berlin",
    "Amsterdam", "Lisbonne", "New York", "Montréal", "Dakar", "Alger", "Tunis", "Tokyo",
    "la France", "l'Espagne", "l'Italie", "l'Allemagne", "la Belgique", "la Suisse",
    "le Portugal", "l'Angleterre", "le Maroc", "l'Algérie", "le Sénégal", "le Canada",
    "les États-Unis", "la Chine", "le Japon", "le Brésil", "l'Afrique", "l'Europe",
    "la Bretagne", "la Normandie", "la Provence", "l'Alsace", "la Corse", "les Alpes",
    "les Pyrénées", "la Méditerranée", "l'océan Atlantique", "la Seine", "la Loire",
    "la tour Eiffel", "le mont Saint-Michel", "Disneyland",
]
# Share of prompts with an imposed place: an always-imposed place clashed with the
# theme ("la voiture" + "dans le salon" -> "Hugo, respire plus lentement dans la voiture").
PLACE_PROMPT_SHARE: float = 0.5
# Real corpora are dominated by class 5 (downsampled in processing_before_llm.py):
# the synthetic set favours the simple classes.
STRUCTURE_WEIGHTS: dict[int, float] = {1: 0.30, 2: 0.25, 3: 0.20, 4: 0.15, 5: 0.10}

# Only the time of the action: imposing a precise tense ("imparfait", "futur simple")
# produced forced sentences ("Serais-tu allé pêcher hier ?"). The model picks the
# natural form (passé composé or imparfait, futur proche, imperative for an order...).
TENSE_WEIGHTS: dict[str, float] = {"présent": 0.50, "passé": 0.25, "futur": 0.25}

# Questions are central in CAA: as frequent as affirmative sentences (~39% of the
# sentences with the "poser une question" intention, always interrogative).
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
    entite: str | None = None

    def structure(self) -> str:
        """Structure constraint of the target class, with its imposed entity."""
        return STRUCTURES[self.classe_cible].format(entite=self.entite)


@dataclass
class PromptSpec:
    """Shared context of one prompt and the specs of its sentences."""

    theme: str
    lieu: str | None
    locuteur: str
    sentences: list[SentenceSpec]

    def metadata(self, index: int) -> dict:
        """Metadata of the ``index``-th sentence, saved next to its text."""
        sentence = asdict(self.sentences[index])
        return {"theme": self.theme, "lieu": self.lieu, "locuteur": self.locuteur, **sentence}


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    """Draw a key of ``weights`` proportionally to its weight."""
    return rng.choices(list(weights), list(weights.values()))[0]


def sample_sentence_spec(rng: random.Random, classes: list[int], weights: list[float]) -> SentenceSpec:
    """Sample one sentence spec, without contradictory constraints.

    A question is always interrogative ("poser une question ; phrase affirmative"
    would yield an unnatural sentence).
    """
    intention = rng.choice(INTENTIONS)
    temps = weighted_choice(rng, TENSE_WEIGHTS)
    if intention == "poser une question":
        type_phrase = "interrogative"
    else:
        type_phrase = weighted_choice(rng, SENTENCE_TYPE_WEIGHTS)
    classe_cible = rng.choices(classes, weights)[0]
    entite = rng.choice(NAMED_PLACES) if classe_cible in (4, 5) else None
    return SentenceSpec(
        intention=intention,
        classe_cible=classe_cible,
        temps=temps,
        type_phrase=type_phrase,
        entite=entite,
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
            lieu=rng.choice(PLACES) if rng.random() < PLACE_PROMPT_SHARE else None,
            locuteur=rng.choice(SPEAKERS),
            sentences=sentences,
        ))
    return specs
