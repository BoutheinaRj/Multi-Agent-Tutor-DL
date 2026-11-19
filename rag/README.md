# rag/

Responsable : Both — tâches B1-B2 (voir la répartition des tâches).

## B1 — Qdrant + embeddings + recherche hybride

| Fichier | Rôle |
|---|---|
| `store.py` | `VectorStore` : collection Qdrant de `Chunk` (schéma T0), recherche dense filtrable par `course_id`. Embedders : `BgeM3Embedder` (bge-m3, 1024 dim., multilingue) et `HashEmbedder` (factice, pour les tests). |
| `search.py` | `BM25` (lexical, insensible aux accents), `fusion_rrf` (Reciprocal Rank Fusion, k = 60) et `RechercheHybride` (dense + BM25 → RRF → `list[SearchHit]`). |

### Utilisation

```python
from rag.store import VectorStore, BgeM3Embedder
from rag.search import RechercheHybride

store = VectorStore(BgeM3Embedder(), chemin="qdrant_storage")  # ou url="http://localhost:6333"
store.ajouter(chunks)                      # list[schemas.models.Chunk]
recherche = RechercheHybride(store)
hits = recherche.rechercher("Qu'est-ce qu'une clé primaire ?", k=5, course_id="bd_introduction_cotedazur_fr")
```

- **Qdrant sans Docker** : `chemin="qdrant_storage"` (dossier local, ignoré par Git). Avec Docker : `docker run -p 6333:6333 qdrant/qdrant` puis `url="http://localhost:6333"`.
- **bge-m3** est téléchargé au premier encodage (~2,3 Go, mis en cache par Hugging Face).
- Après un ajout ou une suppression de chunks, appeler `recherche.rafraichir()` pour reconstruire l'index BM25.
- B2 : demander `k=20` à `rechercher`, puis reranker et garder les 5 premiers. B4 : `recherche.dense(...)` sert de version « avant ».

### Vérifier

```bash
python -m pytest tests/test_rag_b1.py -q              # sans modèle (HashEmbedder, Qdrant en mémoire)
python -m rag.search "Qu'est-ce qu'une clé primaire ?" --hash   # démo sans modèle
python -m rag.search "how to move a VM without downtime"         # démo avec bge-m3
```
