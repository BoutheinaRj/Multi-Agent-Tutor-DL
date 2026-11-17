# eval/

Responsable : Ons + Both — tâches C2, B4 (voir la répartition des tâches).

## C2 — Jeu d'évaluation (`dataset.json`)

Format défini dans `schema.py` (`QuestionEval`, `JeuEvaluation`), vérifié par `tests/test_eval_dataset.py`.

| Champ | Description |
|---|---|
| `id` | `<course_id>__qNN` |
| `course_id` | cours du corpus (présent dans `data/corpus/inventaire_*.csv`) |
| `auteur` | `ons` ou `both` |
| `type` | `factuelle`, `comprehension`, `figure`, `hors_cours` |
| `langue` | `fr` ou `en` (langue du cours) |
| `question`, `reponse_reference` | question et réponse attendue, tirée du cours |
| `slides` | numéros des slides sources ; vide pour `hors_cours` |
| `relu_par` | relecture croisée : l'autre membre (`ons` ↔ `both`) |

Règles :
- ~10 questions par cours du noyau (`data/corpus/noyau_ons.json`, noyau de Both à venir) ;
- les 4 types dans chaque cours ;
- `hors_cours` : réponse de référence = « L'information n'est pas dans le cours. » (refus attendu, B3) ;
- les slides citées doivent exister dans le cours.

Avancement :
- **Ons : 100 questions** sur les 10 cours du noyau (`noyau_ons.json`), 50 FR / 50 EN :
  46 factuelles, 34 de compréhension, 10 sur une figure, 10 hors cours. À relire par Both (`relu_par`).
- Les questions « figure » s'appuient sur le texte des slides : à vérifier sur les images lors de la relecture.
- Pour les cours EN, la réponse attendue hors cours reste la phrase de refus commune (en français).
- **Both** : ~60 questions sur son noyau, à venir.
