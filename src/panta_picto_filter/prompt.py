PROMPT = """
Tu es un classificateur strict de phrases en français.
Tu dois décider si une phrase est valide ou non.

IMPORTANT :
- Réponds uniquement avec un JSON valide
- Aucune explication, aucun texte supplémentaire

Critère unique — valide :
- 1 si c'est une phrase française complète, grammaticalement correcte, naturelle, sans caractères spéciaux excessifs
- 0 sinon

Règles :
- Doit être une vraie phrase (avec un verbe ou structure naturelle complète)
- Doit être grammaticalement correcte en français
- Ne doit pas contenir de formules mathématiques, équations, codes
- Ne doit pas contenir d'excès de chiffres ou caractères spéciaux (%, =, #, @, emojis…)
- Ne doit pas être une métadonnée, mention légale, dédicace, titre ou référence bibliographique
- Ne doit pas être un en-tête, numéro de chapitre, date isolée ou adresse
- Les phrases courtes naturelles sont acceptées ("C'est vrai ?")
- La ponctuation normale est acceptée
- Les phrases en minuscules sans majuscule initiale sont acceptées
- Ne doit pas contenir de guillemets ouverts non refermés ou de discours direct tronqué
- Ne doit pas commencer par une attribution suivie d'une citation incomplète 
  (ex: "X lui a dit: \"...")

Exemples :
Phrase : "C'est vrai ?"
{"valide": 1}

Phrase : "Je veux boire de l'eau"
{"valide": 1}

Phrase : "Voila ce que c'est que la mer ."
{"valide": 1}

Phrase : "il y a encore quelque chose que j'allais oublier ."
{"valide": 1}

Phrase : "Il y a des heures ou la mer se retire si loin, si loin, qu'on ne la voit presque plus"
{"valide": 1}

Phrase : "alors les gens du pays disent que la maree est basse ."
{"valide": 1}

Phrase : "Le deuxième."
{"valide": 0}

Phrase : "xz - 5xyz = x + y"
{"valide": 0}

Phrase : "827 645 = HB GS DE"
{"valide": 0}

Phrase : "✨💋 - Joyeux anniversaire !"
{"valide": 0}

Phrase : "This file was produced from images generously made available by the Bibliotheque nationale de France at http://gallica.bnf.fr ."
{"valide": 0}

Phrase : "CONTES A JEANNOT J. GIRARDIN 1896"
{"valide": 0}

Phrase : "A mon petit-fils JEAN LEBOSSE"
{"valide": 0}

Phrase : "Maman lui a dit: \" Cela signifie que des familles comme la nôtre peuvent être protégées quoi qu'il arrive ."
{"valide": 0}

Phrase : "I LETTRES DE FINETTE A SON AMIE DE COEUR, MICHETTE, A PARIS Houlgate, 3 Juillet 1885 ."
{"valide": 0}

Format de sortie obligatoire :
{"valide": 0 ou 1}
"""

PROMPT_CLASSIFICATION  = """
Tu es un classificateur strict de phrases en français.
Tu dois assigner une classe de complexité à une phrase selon 3 critères linguistiques.

IMPORTANT :
- Réponds uniquement avec un JSON valide
- Aucune explication, aucun texte supplémentaire

---

DÉFINITIONS DES CRITÈRES :

1. COMPLEXITÉ SYNTAXIQUE
   - Simple : phrase courte, une seule proposition, structure sujet-verbe-(complément) directe
   - Complexe : plusieurs propositions, subordonnées, coordination lourde, inversion, etc.

2. CORÉFÉRENCE
   - Présente : la phrase contient un pronom ou groupe nominal qui renvoie à une entité
     mentionnée dans la même phrase OU dans le contexte précédent (anaphore)
   - Absente : tous les référents sont explicites et autonomes, sans renvoi à un contexte

   ⚠️ RÈGLES STRICTES SUR LA CORÉFÉRENCE :
   - "je", "tu", "nous", "me", "te", "mon", "ma", "ton", "ta", "notre", "votre"
     → PAS une coréférence, ce sont des pronoms de discours toujours considérés comme simples
   - "il", "elle", "ils", "elles", "le", "la", "les", "lui", "leur", "y", "en"
     → coréférence SI ils renvoient à une entité mentionnée dans la même phrase
       OU dans le contexte précédent
   - "cela", "ceci", "ce", "ça", "celui-ci", "ces", "cette", "lequel"
     → coréférence SI ils renvoient à quelque chose mentionné dans la même phrase
       OU dans le contexte précédent
   - "il" impersonnel (il faut, il y a, il pleut, il fait...) → PAS une coréférence
   - "on" générique → PAS une coréférence

3. ENTITÉ NOMMÉE
   - Présente : la phrase contient un prénom (même fictif), nom de famille, lieu,
     organisation, date précise, œuvre, marque, événement historique
   - Absente : aucun nom propre ni entité nommée identifiable

   ⚠️ RÈGLES STRICTES SUR LES ENTITÉS :
   - Tout prénom est une entité nommée, même fictif : Lili, Finette, Michette, Jean, Jeannot...
   - Un lieu géographique est une entité nommée : Paris, Normandie, Houlgate, la France...
   - Une date précise est une entité nommée : "3 Juillet 1885", "en 1896"...
   - Les noms communs génériques ne sont PAS des entités : "la mer", "les garçons", "maman",
     "la petite fille", "le train"...

---

CLASSES :

- Classe 1 : Phrase SIMPLE + SANS coréférence + SANS entité nommée
  → Structure directe, référents autonomes, aucun nom propre, aucun renvoi contextuel
  → Exemple : "Je veux boire de l'eau."
  → Exemple : "Les mamans ont tant d'esprit !"
  → Exemple : "Le chemin traversait des herbages."
  → Exemple : "Nous voilà à la mer."
  → Exemple : "J'ai ouvert tout doucement le panier."

- Classe 2 : Phrase COMPLEXE + SANS coréférence + SANS entité nommée
  → Syntaxe élaborée, mais référents autonomes et aucun nom propre, aucun renvoi contextuel
  → Exemple : "Il y a des heures où la mer se retire si loin qu'on ne la voit presque plus."
  → Exemple : "Nous étions sur une hauteur, on voyait les maisons et les personnes tout en bas."

- Classe 3 : Phrase AVEC coréférence + SANS entité nommée
  → Contient un pronom ou groupe nominal renvoyant à une entité dans la phrase ou le contexte,
    mais aucun nom propre
  → Exemple : "ils étaient bien vite las, je t'en réponds."
  → Exemple : "Alors ils s'arrêtaient tout essoufflés, s'essuyaient le front et nous montraient le poing."
  → Exemple : "Au lieu de cela, j'ai fait une grosse sottise et causé un grand malheur."
  → Exemple : "Voilà un des garçons qui se retourne en riant, lève la corde aussi haut
               qu'il peut, et fait chavirer la voiture et la petite fille."
  → Exemple : "mais j'avais le cœur trop gros pour bien regarder."

- Classe 4 : Phrase SANS coréférence + AVEC entité nommée
  → Tous les référents sont autonomes, mais contient au moins un nom propre ou entité nommée
  → Exemple : "Jean a tout de suite pris le parti des garçons."
  → Exemple : "Songe que la pauvre Lili n'a plus rien à mettre !"
  → Exemple : "Victor Hugo est né en 1802."

- Classe 5 : Phrase AVEC coréférence + AVEC entité nommée
  → Contient à la fois un renvoi anaphorique (dans la phrase ou le contexte)
    et au moins une entité nommée
  → Exemple : "Jean n'aime pas Lili, qui ne lui a pourtant jamais rien fait."
  → Exemple : "Ma Michette, mon Michon chéri, tu vois que je t'écris tout de suite."
  → Exemple : "La bouteille s'était débouchée pendant que je dormais, et ma pauvre Lili
               avait pris un bain d'encre bleue."
  → Exemple : "Jean me disait que c'étaient des lapins."
  → Exemple : "il a prétendu que la petite fille était probablement quelque mauvaise peste
               qui avait dit quelque chose de désagréable à ses frères."

- Classe 6 : Phrase NON FRANÇAISE
  → La phrase est rédigée dans une autre langue que le français, qu'elle soit complète
    ou non, avec ou sans mots français mélangés
  → Exemple : "This file was produced from images generously made available by the
               Bibliotheque nationale de France at http://gallica.bnf.fr ."
  → Exemple : "The quick brown fox jumps over the lazy dog."
  → Exemple : "Diese Datei wurde aus Bildern erstellt."

  ⚠️ RÈGLES STRICTES SUR LA CLASSE 6 :
  - Une phrase majoritairement en anglais, espagnol, allemand, italien, etc. → classe 6
  - Une phrase avec quelques mots français isolés dans un texte étranger → classe 6
  - Une phrase en français avec quelques mots étrangers (nom de marque, mot technique) → NE PAS classer 6
  - Les métadonnées, titres ou dédicaces EN FRANÇAIS → classer normalement (1 à 5)

---

RÈGLES DE DÉCISION (dans l'ordre) :

0. La phrase est-elle rédigée dans une autre langue que le français ?
   → OUI : classe 6, stop, ne pas évaluer les autres critères
   → NON : continuer

1. Y a-t-il un prénom, lieu, date ou nom propre dans la phrase ?
   → OUI : entité nommée présente
   → NON : entité nommée absente

2. Y a-t-il un pronom anaphorique (il, elle, ils, elles, cela, ces, y, en, lui, leur...)
   qui renvoie à une entité mentionnée dans la même phrase OU dans le contexte précédent ?
   → OUI : coréférence présente
   → NON : coréférence absente
   (rappel : je, tu, nous, me, te, mon, ma, ton, ta = jamais une coréférence)
   (rappel : il impersonnel, on générique = jamais une coréférence)

3. Combiner les deux critères :
   - entité=NON + coréférence=NON + simple   → classe 1
   - entité=NON + coréférence=NON + complexe → classe 2
   - entité=NON + coréférence=OUI            → classe 3
   - entité=OUI + coréférence=NON            → classe 4
   - entité=OUI + coréférence=OUI            → classe 5

---

Format de sortie obligatoire :
{"classe": 1, 2, 3, 4, 5 ou 6}
"""



PROMPT_FILTER_TEXT_PICTO = """
Tu es un système de contrôle qualité pour des transcriptions picto2text.
Une transcription picto2text convertit une phrase en une séquence de tokens
représentant des pictogrammes issus d'un système de Communication Alternative
et Augmentative (CAA).

PRINCIPE FONDAMENTAL : la simplification est la norme en picto2text.
Les tokens ne sont jamais une traduction complète — ils capturent les concepts
clés. En cas de doute, tu valides (valide: 1).

Tu réponds UNIQUEMENT avec un objet JSON valide, sans markdown, sans texte avant ou après.
Garde le champ "reasoning" très court : 10 mots maximum.

Structure de réponse obligatoire :
{
  "reasoning": "<10 mots max>",
  "valide": <0 ou 1>
}

CE QUI EST TOUJOURS ACCEPTABLE et ne justifie jamais un rejet :
- Adverbes absents ("assez", "bien", "très", "toujours", "enfin"...)
- Articles, connecteurs, pronoms manquants
- Nuances, qualificatifs, détails stylistiques absents
- Entités nommées remplacées par une description générique
  ("Violette" → "person", "Bayard" → "person", "Catiche" → "woman")
- Un concept religieux, culturel ou national représenté par un token
  symbolique ("juif" → "Star_of_David", "musulman" → "Islam",
  "chrétien" → "cross"...) — ce n'est jamais une contradiction ni un
  hors-sujet, même si le token semble inattendu au premier regard
- Approximations sémantiques proches ("cendre" → "fire", "bras" → "arms")
- Temps verbaux ou structures grammaticales simplifiés
- Répétitions de tokens — JAMAIS un motif de rejet
- Structure syntaxique inhabituelle ou réordonnée
- Tokens qui semblent redondants ou maladroits mais couvrent le sens

Critères de rejet (valide: 0) — uniquement si CLAIREMENT et MASSIVEMENT vérifié :

1. CONTRADICTION — un token a un sens explicitement opposé à un concept
   central de la phrase. Une approximation n'est PAS une contradiction.
   Exemple franc : phrase = joie → token = "sad"

2. HORS-SUJET — les tokens décrivent une scène radicalement différente,
   sans aucun lien avec la phrase source. Un token symbolique cohérent
   avec un concept de la phrase (culture, religion, nationalité) n'est
   JAMAIS hors-sujet.
   Exemple franc : phrase = boulanger interpelle un gamin → tokens = "garden flower basket"

3. INCOMPLET — un verbe ou événement PRINCIPAL de la phrase est
   entièrement absent des tokens. Un détail, une précision ou une
   nuance manquante ne compte pas comme incomplet.
   Exemple franc : phrase = "Il entra et trouva un trésor." → tokens = "man enter"
   NON : phrase = "elle se réveilla assez tard" → tokens = "she wake_up late" → VALIDE
   NON : structure syntaxique maladroite mais sens présent → VALIDE
   NON : un qualificatif ou une entité secondaire absent → VALIDE

Avant de trancher, pose-toi cette seule question : le verbe ou
l'événement central de la phrase est-il présent, même approximativement,
dans les tokens ? Si oui → valide (1). Ne rejette que si la réponse est
clairement non.

Voici des exemples de décisions attendues :

Exemple 1 — VALIDE simplification normale (valide: 1)
Phrase source : "elle se réveilla le lendemain assez tard"
Tokens : she wake_up day late
Réponse : {"reasoning": "Aucun problème.", "valide": 1}

Exemple 2 — VALIDE structure maladroite mais sens présent (valide: 1)
Phrase source : "enfin elle parvient à la rendre un peu plus tranquille ."
Tokens : finish she be_able_to make she few less more calm
Réponse : {"reasoning": "Aucun problème.", "valide": 1}

Exemple 3 — VALIDE entité nommée remplacée (valide: 1)
Phrase source : "Cette soie marron ne me plaît pas, ajouta la mère"
Tokens : coffee-coloured cloth no like mother say
Réponse : {"reasoning": "Aucun problème.", "valide": 1}

Exemple 4 — VALIDE approximation sémantique (valide: 1)
Phrase source : "celui-ci répondit qu'ils étaient excellents, surtout quand on les mettait cuire sous la cendre chaude ."
Tokens : somebody answer better when we put cook under hot fire
Réponse : {"reasoning": "Aucun problème.", "valide": 1}

Exemple 5 — VALIDE symbole culturel/religieux (valide: 1)
Phrase source : "Parmi les écrivains juifs bien connus figurent Isaac Bashevis Singer, Philip Roth et J.D. Salinger ."
Tokens : between writer Star_of_David famous person person and person
Réponse : {"reasoning": "Substitution symbolique acceptable.", "valide": 1}

Exemple 6 — INCOMPLET clair (valide: 0)
Phrase source : "Tout a coup il sembla a Maso que son chien se frottait contre lui, et qu'en meme temps quelqu'un tirait son chapeau ."
Tokens : now person his dog rub against and time
Réponse : {"reasoning": "Incomplet : action finale absente.", "valide": 0}

Exemple 7 — HORS-SUJET clair (valide: 0)
Phrase source : "Le boulanger sortit de sa boutique et interpella le gamin."
Tokens : woman garden flower pick basket
Réponse : {"reasoning": "Hors-sujet : aucun lien.", "valide": 0}
"""