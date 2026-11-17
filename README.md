# Multi-Agent Tutor for Course Material

Tuteur multi-agent à la manière de NotebookLM : on dépose un cours PPTX ou PDF et on obtient,
slide par slide, une explication pédagogique (3 niveaux), des questions-réponses avec citations
[Slide N], des quiz et flashcards, et des ressources complémentaires.

## Architecture

```
PDF/PPTX → ingestion/ (parse, OCR, VLM, carte du cours) → rag/ (index + recherche hybride + reranker)
        → agents/ (graphe LangGraph : Router, Explainer, Q&A, Quiz, Resources, Critic) → api/ → frontend/
```

Le contrat de données entre modules est décrit dans [`docs/schema.md`](docs/schema.md)
(modèles Pydantic dans `schemas/`).

## Arborescence

| Dossier | Contenu | Responsable |
|---|---|---|
| `schemas/`, `docs/schema.md` | schéma de données commun (T0) | Ons |
| `ingestion/` | parsers, OCR, VLM, carte du cours | Ghayth |
| `rag/` | embeddings, Qdrant, recherche, reranker | Both |
| `agents/`, `prompts/` | graphe et agents | Ons, Both, Ali |
| `api/`, `frontend/` | FastAPI et interface | Ali |
| `eval/` | jeu d'évaluation et benchmark RAGAS | Ons + Both |
| `tools/` | outils d'analyse (`slide_stats.py`) | Ghofrane |
| `data/corpus/` | corpus de test (C1) | Ons + Both |
| `data/corpus_extra/` | corpus complémentaire (G2) | Ghofrane |

## Installation

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
```

## Organisation Git

- `main` : version stable (démos, tag v1.0), aucun push direct.
- `develop` : intégration, reçoit les Pull Requests.
- Une branche par membre : `ons`, `both`, `ghayth`, `ali`, `ghofrane`. Chacun ne modifie que les dossiers de ses tâches.
- Commits préfixés par l'ID de tâche : `[B2] ajout du reranker`.
- PR `<prénom>` → `develop`, relue par Ons (ou par Both pour le code d'Ons).
