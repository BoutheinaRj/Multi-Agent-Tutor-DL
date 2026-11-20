"""A1 — API FastAPI du tuteur, branchée sur le tuteur complet (O5, ``agents/tuteur.py``).

``POST /upload`` lance l'ingestion de Ghayth (H1 → H2 → H3) et indexe le cours pour le RAG (B1-B2) ;
``GET /slide/{id}/explain`` et ``POST /ask`` passent par le graphe (router → Explainer O2 / Q&A B3
→ Critic O3). Le cours d'exemple ``schemas/exemples/exemple_cours.json`` reste chargé au démarrage.
``GET /resources`` utilise
l'agent Resources (A4, catalogue local), ``GET /quiz`` et ``GET /flashcards`` l'agent Quiz (A2),
``/flashcards/save|due|export`` et ``/flashcards/{id}/review`` la révision espacée SM-2 (A6).

Lancement : ``uvicorn api.main:app --reload`` puis http://localhost:8000/docs
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi import Path as PathParam
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from agents import srs
from agents.quiz import brancher_cours, charger_cours, generer_flashcards, generer_quiz_detaille
from agents.resources import charger_slide, chercher_ressources
from agents.tuteur import Tuteur, tuteur_partage
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
    TutorState,
)

EXEMPLE_COURS = Path(__file__).resolve().parent.parent / "schemas" / "exemples" / "exemple_cours.json"
EXTENSIONS_ACCEPTEES = {".pdf": "pdf", ".pptx": "pptx"}
DOSSIER_DEPOTS = Path(__file__).resolve().parent.parent / "data" / "raw" / "depots"
TAILLE_MAX_DEPOT = 50 * 1024 * 1024
log = logging.getLogger(__name__)

# Origines du frontend en développement (Vite, CRA, Streamlit).
ORIGINES_FRONTEND = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8501",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8501",
    # Maquettes D2 servies en local (python -m http.server 8765 --directory docs/maquettes)
    "http://localhost:8765",
    "http://127.0.0.1:8765",
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
)


def tuteur() -> Tuteur:
    """Le tuteur complet (O5), avec le cours d'exemple et les cours chargés par l'API."""
    t = tuteur_partage()
    for cours in COURS.values():
        if cours.id not in t.cours:
            t.ajouter_cours(cours)
    return t


def _course_id_depuis(nom: str) -> str:
    """Identifiant de cours valide (minuscules ASCII, chiffres, « _ ») tiré du nom du fichier."""
    import unicodedata

    base = unicodedata.normalize("NFKD", Path(nom).stem).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base).strip("_")
    return base or "cours"


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
async def upload(fichier: UploadFile = File(...), rapide: bool | None = None) -> Course:
    """Recevoir un PDF/PPTX, l'ingérer (H1 → H2 → H3) et l'indexer : le cours est prêt pour les agents.

    ``rapide`` : texte seul, sans rendu, OCR ni VLM (par défaut : ``INGESTION_RAPIDE`` ou le jeu
    de modèles du tuteur, voir ``agents/tuteur.py``).
    """
    extension = Path(fichier.filename or "").suffix.lower()
    if extension not in EXTENSIONS_ACCEPTEES:
        raise HTTPException(status_code=415, detail="Seuls les fichiers PDF et PPTX sont acceptés")
    contenu = await fichier.read()
    if len(contenu) > TAILLE_MAX_DEPOT:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (50 Mo au plus)")
    DOSSIER_DEPOTS.mkdir(parents=True, exist_ok=True)
    course_id = _course_id_depuis(fichier.filename or "cours")
    chemin = DOSSIER_DEPOTS / f"{course_id}{extension}"
    chemin.write_bytes(contenu)
    try:
        cours = await run_in_threadpool(tuteur().ingerer, chemin, rapide=rapide, course_id=course_id)
    except Exception as e:  # noqa: BLE001 - fichier illisible : message clair plutôt qu'une 500
        log.warning("ingestion impossible pour %s : %s", chemin.name, e)
        raise HTTPException(status_code=422, detail=f"Ce fichier n'a pas pu être lu : {e}") from e
    COURS[cours.id] = cours
    return cours


@app.get("/course/{course_id}", response_model=Course)
def get_course(course_id: str) -> Course:
    return _cours(course_id)


@app.get("/slide/{slide_id}/explain", response_model=AgentResponse)
def explain(
    slide_id: Annotated[str, PathParam(pattern=SLIDE_ID_PATTERN)],
    niveau: Niveau = "intermediaire",
) -> AgentResponse:
    """Explication de la slide par l'Explainer (O2) au niveau demandé, vérifiée par le Critic (O3)."""
    slide = _slide_par_id(slide_id)
    return tuteur().expliquer(slide.course_id, slide.numero, niveau)


@app.post("/ask", response_model=AgentResponse)
def ask(requete: AskRequest) -> AgentResponse:
    """Question sur le cours : le router choisit l'agent (Q&A B3 par défaut), puis le Critic vérifie."""
    slide = _slide(requete.course_id, requete.slide_courante)
    return tuteur().demander(slide.course_id, slide.numero, requete.question, requete.niveau, requete.langue)


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
