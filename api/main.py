"""A1 — API FastAPI du tuteur, avec des données factices.

Les réponses viennent de ``schemas/exemples/exemple_cours.json`` en attendant
le branchement de l'ingestion, du RAG et des agents.

Lancement : ``uvicorn api.main:app --reload`` puis http://localhost:8000/docs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi import Path as PathParam
from fastapi.middleware.cors import CORSMiddleware

from api.models import QCM, AskRequest, Ressource
from schemas.models import (
    SLIDE_ID_PATTERN,
    AgentResponse,
    Course,
    Niveau,
    Slide,
    Source,
)

EXEMPLE_COURS = Path(__file__).resolve().parent.parent / "schemas" / "exemples" / "exemple_cours.json"
EXTENSIONS_ACCEPTEES = {".pdf": "pdf", ".pptx": "pptx"}

# Origines du frontend en développement (Vite, CRA, Streamlit).
ORIGINES_FRONTEND = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8501",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8501",
]


def charger_cours_exemple() -> Course:
    """Charger et valider le cours factice."""
    return Course.model_validate(json.loads(EXEMPLE_COURS.read_text(encoding="utf-8")))


COURS: dict[str, Course] = {}
_exemple = charger_cours_exemple()
COURS[_exemple.id] = _exemple

app = FastAPI(
    title="Tuteur multi-agent — API",
    version="0.1.0",
    description="API factice (A1) : les réponses utilisent un cours d'exemple.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINES_FRONTEND,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cours(course_id: str) -> Course:
    cours = COURS.get(course_id)
    if cours is None:
        raise HTTPException(status_code=404, detail=f"Cours inconnu : {course_id}")
    return cours


def _slide(course_id: str, numero: int) -> Slide:
    cours = _cours(course_id)
    if not 1 <= numero <= cours.nombre_slides:
        raise HTTPException(
            status_code=404,
            detail=f"Slide {numero} hors limites (1..{cours.nombre_slides}) pour {course_id}",
        )
    return cours.slides[numero - 1]


def _slide_par_id(slide_id: str) -> Slide:
    course_id, _, numero = slide_id.rpartition("__s")
    return _slide(course_id, int(numero))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=Course)
async def upload(fichier: UploadFile = File(...)) -> Course:
    """Recevoir un PDF/PPTX et renvoyer un cours factice (ingestion non branchée)."""
    extension = Path(fichier.filename or "").suffix.lower()
    if extension not in EXTENSIONS_ACCEPTEES:
        raise HTTPException(status_code=415, detail="Seuls les fichiers PDF et PPTX sont acceptés")
    await fichier.read()  # Le contenu sera transmis à l'ingestion (H1).
    return _cours(_exemple.id)


@app.get("/course/{course_id}", response_model=Course)
def get_course(course_id: str) -> Course:
    return _cours(course_id)


PREFIXES_NIVEAU: dict[str, str] = {
    "debutant": "En termes simples",
    "intermediaire": "En résumé",
    "avance": "Plus formellement",
}


@app.get("/slide/{slide_id}/explain", response_model=AgentResponse)
def explain(
    slide_id: Annotated[str, PathParam(pattern=SLIDE_ID_PATTERN)],
    niveau: Niveau = "intermediaire",
) -> AgentResponse:
    """Explication factice d'une slide, adaptée au niveau demandé."""
    slide = _slide_par_id(slide_id)
    contenu = slide.texte or slide.titre
    return AgentResponse(
        agent="explainer",
        reponse=(
            f"{PREFIXES_NIVEAU[niveau]} : la slide « {slide.titre} » explique ceci. "
            f"{contenu} [Slide {slide.numero}]"
        ),
        sources=[Source(course_id=slide.course_id, numero=slide.numero, extrait=contenu)],
    )


@app.post("/ask", response_model=AgentResponse)
def ask(requete: AskRequest) -> AgentResponse:
    """Réponse factice à une question, citant la slide courante."""
    slide = _slide(requete.course_id, requete.slide_courante)
    contenu = slide.texte or slide.titre
    return AgentResponse(
        agent="qa",
        reponse=(
            f"Réponse factice ({requete.niveau}, {requete.langue}) à « {requete.question} » : "
            f"{contenu} [Slide {slide.numero}]"
        ),
        sources=[Source(course_id=slide.course_id, numero=slide.numero, extrait=contenu)],
    )


@app.get("/quiz", response_model=list[QCM])
def quiz(
    course_id: str,
    slide: Annotated[int, Query(ge=1)],
) -> list[QCM]:
    """QCM factices construits à partir de la slide demandée."""
    s = _slide(course_id, slide)
    source = Source(course_id=s.course_id, numero=s.numero, extrait=s.texte)
    return [
        QCM(
            question=f"Quel est le sujet principal de la slide « {s.titre} » ?",
            choix=[s.titre, "Les réseaux de neurones", "Le clustering", "La virtualisation"],
            bonne_reponse=0,
            explication=f"Voir [Slide {s.numero}].",
            source=source,
        ),
        QCM(
            question="Cette affirmation provient-elle de la slide ? « " + (s.texte or s.titre) + " »",
            choix=["Vrai", "Faux"],
            bonne_reponse=0,
            explication=f"L'affirmation est reprise de [Slide {s.numero}].",
            source=source,
        ),
    ]


@app.get("/resources", response_model=list[Ressource])
def resources(
    slide_id: Annotated[str, Query(pattern=SLIDE_ID_PATTERN)],
) -> list[Ressource]:
    """Ressources factices liées à une slide."""
    s = _slide_par_id(slide_id)
    sujet = s.titre or "le cours"
    return [
        Ressource(
            titre=f"Vidéo d'introduction : {sujet}",
            url="https://www.youtube.com/results?search_query=" + sujet.replace(" ", "+"),
            type="video",
            description="Ressource factice (A1).",
        ),
        Ressource(
            titre=f"Article : {sujet}",
            url="https://fr.wikipedia.org/w/index.php?search=" + sujet.replace(" ", "+"),
            type="article",
            description="Ressource factice (A1).",
        ),
    ]
