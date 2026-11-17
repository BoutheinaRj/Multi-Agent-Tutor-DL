# agents/

Responsable : Ons, Both, Ali — tâches O1-O3, B3, A2, A4, A6 (voir la répartition des tâches).

## O1 — Graphe LangGraph (`graph.py`)

```
START → router → explainer | qa | quiz | resources → END
```

- **État partagé** : `TutorState` (`schemas/models.py`, T0) : `course_id`, `slide_courante`, `niveau`,
  `langue_reponse`, `historique`, `question`, `intention`, `reponse`, `sources`, `iterations_critic`.
- **Router** : garde l'`intention` si l'API l'impose (ex. `GET /slide/{id}/explain` → `expliquer`),
  sinon la déduit de la question par mots-clés FR/EN (`classer_intention`, provisoire, remplaçable par un LLM).
  Sans question : `expliquer`.
- **Agents** : des bouchons renvoient une réponse fixe `[agent] … [Slide N]`, une source et l'historique.

### Brancher son agent (Both, Ali)

Un agent est une fonction `(TutorState) -> dict` qui renvoie les champs modifiés :

```python
from agents.graph import construire_graphe, executer
from schemas import Source, TutorState

def agent_qa(state: TutorState) -> dict:
    passages = search(state.question, state.course_id, k=5)      # rag/ (B2)
    return {"reponse": "…", "sources": [Source(course_id=state.course_id, numero=3)]}

graphe = construire_graphe({"question": agent_qa})              # les autres restent des bouchons
final = executer(TutorState(course_id="ml_x_fr", slide_courante=3, question="Pourquoi ?"), graphe)
```

| Intention | Nœud | Responsable |
|---|---|---|
| `expliquer` | `explainer` | Ons (O2) |
| `question` | `qa` | Both (B3) |
| `quiz` | `quiz` | Ali (A2) |
| `ressources` | `resources` | Ali (A4) |

Le Critic (O3) s'insérera entre les agents et `END`. Tests : `tests/test_graph.py`.
