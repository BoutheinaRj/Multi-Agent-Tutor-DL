# api/

Responsable : Ali — tâches A1, A3, A7 (voir la répartition des tâches).

## A1 — API factice

Routes (données factices tirées de `schemas/exemples/exemple_cours.json`) :

| Méthode | Route | Réponse |
|---|---|---|
| POST | `/upload` (champ `fichier`, PDF/PPTX) | `Course` |
| GET | `/course/{id}` | `Course` |
| GET | `/slide/{id}/explain?niveau=debutant\|intermediaire\|avance` | `AgentResponse` |
| POST | `/ask` (body : `course_id`, `slide_courante`, `question`, `niveau`, `langue`) | `AgentResponse` avec sources `[Slide N]` |
| GET | `/quiz?course_id=&slide=` | `list[QCM]` |
| GET | `/resources?slide_id=` | `list[Ressource]` |

Les types viennent de `schemas/models.py` ; `QCM`, `Ressource` et `AskRequest`, absents du
contrat commun, sont définis dans `api/models.py`. CORS est ouvert aux origines locales du
frontend (ports 3000, 5173, 8501).

### Lancer

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Puis ouvrir http://localhost:8000/docs.

### Tester

```bash
pytest tests/test_api.py
```
