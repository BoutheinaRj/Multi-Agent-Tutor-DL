"""A1 — API FastAPI du tuteur, avec des données factices.

Les réponses viennent de ``schemas/exemples/exemple_cours.json`` en attendant
le branchement de l'ingestion, du RAG et des agents ; ``GET /resources`` utilise déjà
l'agent Resources (A4, catalogue local), ``GET /quiz`` et ``GET /flashcards`` l'agent Quiz (A2),
``/flashcards/save|due|export`` et ``/flashcards/{id}/review`` la révision espacée SM-2 (A6).

Lancement : ``uvicorn api.main:app --reload`` puis http://localhost:8000/docs
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi import Path as PathParam
from fastapi.middleware.cors import CORSMiddleware

from agents import srs
from agents.quiz import brancher_cours, charger_cours, generer_flashcards, generer_quiz_detaille
from agents.resources import charger_slide, chercher_ressources
from api.models import (
    QCM,
    AskRequest,
    CarteSRS,
    Flashcard,
    NiveauBloom,
    Ressource,
    ReviewRequest,
    SaveFlashcardsRequest,
)
from schemas.models import (
    COURSE_ID_PATTERN,
    SLIDE_ID_PATTERN,
    AgentResponse,
    Course,
    Langue,
    Niveau,
    Slide,
    Source,
    TutorState,
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
brancher_cours(COURS.get)  # l'agent Quiz (A2) voit les cours chargés par l'API

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
    # Lisibles par le frontend (A5) : raison d'un quiz vide, nom du fichier Anki exporté.
    expose_headers=["X-Quiz-Message", "Content-Disposition"],
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
    response: Response,
    course_id: str,
    slide: Annotated[int | None, Query(ge=1)] = None,
    n: Annotated[int, Query(ge=1, le=10)] = 3,
    niveau_bloom: NiveauBloom | None = None,
    langue: Langue | None = None,
) -> list[QCM]:
    """QCM générés par l'agent Quiz (A2) avec le LLM local, sur une slide ou tout le cours.

    Liste vide (et en-tête ``X-Quiz-Message``) si le LLM local est indisponible.
    """
    _verifier_cible(course_id, slide)
    resultat = generer_quiz_detaille(course_id, slide, n, niveau_bloom, langue=langue)
    if resultat.message:
        response.headers["X-Quiz-Message"] = quote(resultat.message)
    return resultat.qcm


@app.get("/flashcards", response_model=list[Flashcard])
def flashcards(
    course_id: str,
    slide: Annotated[int | None, Query(ge=1)] = None,
    n: Annotated[int, Query(ge=1, le=10)] = 5,
    langue: Langue | None = None,
) -> list[Flashcard]:
    """Flashcards de l'agent Quiz (A2) ; sans LLM, une carte titre → texte par slide."""
    _verifier_cible(course_id, slide)
    return generer_flashcards(course_id, slide, n, langue=langue)


UtilisateurQuery = Annotated[str, Query(min_length=1, max_length=100)]


@app.post("/flashcards/save", response_model=list[CarteSRS])
def flashcards_save(requete: SaveFlashcardsRequest) -> list[CarteSRS]:
    """Mémoriser des flashcards (A2) pour un utilisateur (A6) ; une carte connue n'est pas dupliquée."""
    return srs.ajouter_cartes(requete.user, requete.flashcards)


@app.get("/flashcards/due", response_model=list[CarteSRS])
def flashcards_due(
    user: UtilisateurQuery,
    date_revision: Annotated[date | None, Query(alias="date")] = None,
    course_id: Annotated[str | None, Query(pattern=COURSE_ID_PATTERN)] = None,
) -> list[CarteSRS]:
    """Cartes de l'utilisateur à réviser au plus tard à ``date`` (défaut : aujourd'hui)."""
    return srs.cartes_a_reviser(user, date_revision, course_id)


@app.post("/flashcards/{carte_id}/review", response_model=CarteSRS)
def flashcards_review(carte_id: int, requete: ReviewRequest) -> CarteSRS:
    """Noter une révision (``qualite`` 0..5) et replanifier la carte selon SM-2."""
    try:
        return srs.enregistrer_revision(requete.user, carte_id, requete.qualite)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=erreur.args[0]) from erreur


@app.get("/flashcards/export")
def flashcards_export(
    course_id: Annotated[str, Query(pattern=COURSE_ID_PATTERN)],
    user: UtilisateurQuery,
) -> Response:
    """Télécharger le deck Anki (.apkg) des cartes de l'utilisateur pour un cours."""
    try:
        contenu = srs.exporter_apkg(user, course_id)
    except LookupError as erreur:
        raise HTTPException(status_code=404, detail=erreur.args[0]) from erreur
    return Response(
        content=contenu,
        media_type="application/apkg",
        headers={"Content-Disposition": f'attachment; filename="{course_id}.apkg"'},
    )


def _verifier_cible(course_id: str, slide: int | None) -> None:
    """404 si le cours (API, ``data/processed`` ou exemple) ou la slide n'existe pas."""
    cours = charger_cours(course_id)
    if cours is None:
        raise HTTPException(status_code=404, detail=f"Cours inconnu : {course_id}")
    if slide is not None and not 1 <= slide <= cours.nombre_slides:
        raise HTTPException(
            status_code=404,
            detail=f"Slide {slide} hors limites (1..{cours.nombre_slides}) pour {course_id}",
        )


@app.get("/resources", response_model=list[Ressource])
def resources(
    slide_id: Annotated[str, Query(pattern=SLIDE_ID_PATTERN)],
    niveau: Niveau = "intermediaire",
    langue: Langue = "fr",
) -> list[Ressource]:
    """Ressources externes pour une slide (A4) : catalogue local, sans appel réseau."""
    s = _slide_par_id(slide_id)
    state = TutorState(course_id=s.course_id, slide_courante=s.numero, niveau=niveau, langue_reponse=langue)
    return chercher_ressources(state, charger=_slide_connue)


def _slide_connue(course_id: str, numero: int) -> Slide | None:
    """Slide d'un cours chargé par l'API, sinon d'un cours ingéré dans ``data/processed``."""
    cours = COURS.get(course_id)
    if cours is not None and 1 <= numero <= cours.nombre_slides:
        return cours.slides[numero - 1]
    return charger_slide(course_id, numero)
