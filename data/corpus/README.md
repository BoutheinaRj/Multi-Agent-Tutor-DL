# C1 — Corpus de test

Objectif : 5 à 10 cours PPTX et PDF, en français et en anglais, de 15 à 60 slides chacun,
pour tester l'ingestion (H1–H3), le RAG (B1–B2) et les agents.

- **Ons** : cours riches en schémas, diagrammes et formules (maths, ML, réseaux).
- **Both** : cours riches en texte, dont au moins un PDF scanné (test de l'OCR).

Corpus complémentaire d'autres matières : `data/corpus_extra/` (Ghofrane, G2). Ne pas reprendre ces cours ici.

## Règles pour collecter en parallèle

1. **Fichiers à plat** dans `data/corpus/`, nommés `<matiere>_<sujet>_<langue>.<pdf|pptx>` :
   minuscules ASCII, chiffres et `_`, sans accent. Le nom sans extension sert de `course_id`
   (voir `docs/schema.md`). Exemple : `ml_reseaux_neurones_fr.pptx`.
2. **Préfixes réservés**, pour éviter les doublons :
   - Ons : `maths_`, `ml_`, `reseaux_` ;
   - Both : les autres matières textuelles (`histoire_`, `droit_`, `bio_`…) et `scan_` pour un PDF scanné.
3. **Un inventaire par personne** : `inventaire_ons.csv` et `inventaire_both.csv`. Chacune ne modifie que le sien.
   Ce README n'est modifié que par Ons.
4. **Ce qui ne va pas dans Git** : fichiers de plus de 20 Mo, et cours sans licence qui autorise la redistribution
   (supports internes, etc.). Ils vont dans `data/corpus/_local/` (ignoré par Git) avec seulement leur ligne dans l'inventaire.
5. Commits préfixés `[C1]`, par exemple `[C1] ajout ml_reseaux_neurones_fr`.

## Format des inventaires

Mêmes premières colonnes que `data/corpus_extra/inventaire.csv`, puis des colonnes ajoutées :

| Colonne | Valeurs |
|---|---|
| `fichier` | nom du fichier (`_local/...` s'il n'est pas versionné) |
| `titre` | titre du cours |
| `source` | URL d'origine |
| `format` | `PDF` ou `PPTX` |
| `langue` | `fr`, `en`, `ar` ou `mixte` |
| `nombre_slides` | calculé avec `python tools/slide_stats.py <fichier>` |
| `licence` | ex. `CC BY-NC-SA 4.0`, `inconnue` |
| `collecte_par` | `ons` ou `both` |
| `contenu` | `figures`, `formules`, `texte`, combinés par `+` |
| `scanne` | `oui` ou `non` |
| `date_collecte` | `AAAA-MM-JJ` |

## Crédits

- `reseaux_introduction_kurose_en.pptx` : slides identiques à celles de J.F. Kurose et K.W. Ross,
  *Computer Networking: A Top-Down Approach*, 9e édition, chapitre 1 (V9.0).
  © 1996-2025 J.F. Kurose et K.W. Ross, tous droits réservés.
  Source : https://gaia.cs.umass.edu/kurose_ross/ppt.php — diffusées par les auteurs pour un usage libre,
  à condition de citer la source et leur copyright.
