# C1 — Corpus de test

Objectif initial : 5 à 10 cours PPTX et PDF, en français et en anglais, de 15 à 60 slides chacun
(élargi : le plus de cours possible, de sources variées),
pour tester l'ingestion (H1–H3), le RAG (B1–B2) et les agents.

- **Ons** : cours riches en schémas, diagrammes et formules (maths, ML, réseaux).
- **Both** : cours riches en texte, dont au moins un PDF scanné (test de l'OCR).

Corpus complémentaire d'autres matières : `data/corpus_extra/` (Ghofrane, G2). Ne pas reprendre ces cours ici.

## Règles pour collecter en parallèle

1. **Rangement par langue puis par domaine** : `data/corpus/<langue>/<domaine>/<fichier>`,
   avec `<langue>` = `fr` ou `en` et `<domaine>` = `maths`, `ml`, `dl`, `reseaux` (ou un domaine de Both).
   Fichiers nommés `<domaine>_<sujet>_<source>_<langue>.<pdf|pptx>` : minuscules ASCII, chiffres et `_`,
   sans accent. Le nom sans extension sert de `course_id` (voir `docs/schema.md`) et doit être unique
   dans tout le corpus. Exemple : `en/dl/dl_deep_learning_louppe1_en.pdf`.
   - `maths` : probabilités, algèbre, analyse ;
   - `ml` : apprentissage automatique classique et optimisation (régression, gradient…) ;
   - `dl` : deep learning (réseaux de neurones, CNN, transformers, LLM) ;
   - `reseaux` : réseaux informatiques.
2. **Préfixes réservés**, pour éviter les doublons :
   - Ons : `maths_`, `ml_`, `dl_`, `reseaux_` ;
   - Both : les autres matières textuelles (`histoire_`, `droit_`, `bio_`…) et `scan_` pour un PDF scanné.
3. **Un inventaire par personne** : `inventaire_ons.csv` et `inventaire_both.csv`. Chacune ne modifie que le sien.
   Ce README n'est modifié que par Ons.
4. **Ce qui ne va pas dans Git** : fichiers de plus de 20 Mo, et cours sans licence qui autorise la redistribution
   (supports internes, etc.). Ils vont dans `data/corpus/_local/<langue>/<domaine>/` (ignoré par Git),
   avec seulement leur ligne dans l'inventaire.
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

- `en/reseaux/reseaux_introduction_kurose_en.pptx` : slides identiques à celles de J.F. Kurose et K.W. Ross,
  *Computer Networking: A Top-Down Approach*, 9e édition, chapitre 1 (V9.0).
  © 1996-2025 J.F. Kurose et K.W. Ross, tous droits réservés.
  Source : https://gaia.cs.umass.edu/kurose_ross/ppt.php — diffusées par les auteurs pour un usage libre,
  à condition de citer la source et leur copyright.
- `en/dl/dl_fondements_louppe_en.pdf` et `en/dl/dl_perceptrons_louppe_en.pdf` : slides de Gilles Louppe,
  INFO8010 Deep Learning, Université de Liège (lectures 1 et 2). Source : https://github.com/glouppe/info8010-deep-learning,
  licence BSD-3-Clause.
- `en/dl/dl_introduction_uva_en.pdf` : slides d'Efstratios Gavves, UvA Deep Learning Course, lecture 1 (2019).
  Source : https://uvadlc.github.io, licence Apache-2.0.

## Répartition du corpus d'Ons (2026-11-17)

27 cours, dont 4 versionnés dans Git et 23 dans `_local/` (non versionnés : supports Esprit internes ou licence inconnue).

| Langue | maths | ml | dl | reseaux | Total |
|---|---|---|---|---|---|
| fr | 3 | 4 | 2 | 4 | 13 |
| en | 0 | 5 | 6 | 3 | 14 |
| **Total** | 3 | 9 | 8 | 7 | **27** |

Détail (titre, source, licence, nombre de slides) : `inventaire_ons.csv`.
