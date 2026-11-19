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

## B3 — Agent Q&A avec citations (`qa.py`)

```python
from agents.graph import construire_graphe
from agents.qa import AgentQA
from rag.rerank import BgeReranker, RechercheReranked
from rag.search import RechercheHybride
from rag.store import BgeM3Embedder, VectorStore

store = VectorStore(BgeM3Embedder(), chemin="qdrant_storage")       # cours indexés par python -m rag.index
agent = AgentQA(RechercheReranked(RechercheHybride(store), BgeReranker()))
graphe = construire_graphe({"question": agent})
```

- Recherche B2 (hybride top-20 → reranker top-5) dans le cours courant ; seuls les passages au score ≥ 0,01 (réglable : `QA_SEUIL` dans `.env`) sont gardés ; ce seuil écarte le hors-sujet évident, et le LLM refuse si les passages ne permettent pas de répondre.
- Aucun passage pertinent : réponse « L'information n'est pas dans le cours. » (`eval.schema.REPONSE_HORS_COURS`), sans appeler le LLM.
- Sinon, le LLM local (A0) répond à partir des seuls passages, en citant `[Slide N]` ; les citations de slides absentes des passages sont retirées ; une réponse sans citation reçoit celle du meilleur passage.
- LLM indisponible (`LLMIndisponible`) : repli extractif, le passage le plus pertinent est renvoyé avec sa citation.
- Démo : `python -m agents.qa "Qu'est-ce que la fonction de coût ?"` (cours d'exemple T0, modèles locaux). Tests : `tests/test_qa.py` (LLM fake).
