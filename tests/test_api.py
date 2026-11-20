"""Tests de l'API (A1) branchée sur le tuteur complet (O5) : une assertion par route."""

from __future__ import annotations

import json
import os

# Modèles légers (aucun téléchargement) et pas de LLM réel : les agents passent par leurs replis.
os.environ.setdefault("TUTEUR_MODELES", "leger")

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import QCM, Ressource
from schemas import AgentResponse, Course

client = TestClient(app)

COURSE_ID = "ml_regression_lineaire_fr"
SLIDE_ID = f"{COURSE_ID}__s002"


def _pdf(pages: list[tuple[str, str]]) -> bytes:
    """Un vrai petit PDF (titre en grand, texte dessous) pour l'ingestion H1."""
    import pymupdf

    doc = pymupdf.open()
    for titre, texte in pages:
        page = doc.new_page()
        page.insert_text((72, 90), titre, fontsize=24)
        page.insert_text((72, 150), texte, fontsize=12)
    return doc.tobytes()


@pytest.fixture
def depots_temporaires(tmp_path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Dépôts et sorties de l'ingestion dans un dossier temporaire, pas dans data/."""
    import api.main as api_main

    monkeypatch.setattr(api_main, "DOSSIER_DEPOTS", tmp_path / "depots")
    monkeypatch.setattr(api_main.tuteur(), "dossier_sortie", tmp_path / "processed")
    return tmp_path


@pytest.mark.usefixtures("depots_temporaires")
def test_upload_ingere_et_indexe_le_cours() -> None:
    contenu = _pdf([("Les arbres de decision", "Un arbre de decision partage les donnees selon des seuils."),
                    ("Elagage", "L'elagage retire les branches qui surapprennent.")])
    r = client.post("/upload", files={"fichier": ("Arbres de décision.pdf", contenu, "application/pdf")},
                    params={"rapide": True})
    assert r.status_code == 200, r.text
    cours = Course.model_validate(r.json())
    assert cours.id == "arbres_de_decision" and cours.nombre_slides == 2
    assert cours.slides[0].titre == "Les arbres de decision"
    # Le cours déposé est aussitôt utilisable par les agents.
    assert client.get(f"/course/{cours.id}").status_code == 200
    r = client.post("/ask", json={"course_id": cours.id, "slide_courante": 2,
                                  "question": "Que retire l'elagage ?"})
    assert r.status_code == 200 and AgentResponse.model_validate(r.json()).sources[0].numero == 2


@pytest.mark.usefixtures("depots_temporaires")
def test_upload_fichier_illisible() -> None:
    r = client.post("/upload", files={"fichier": ("cours.pdf", b"%PDF-1.4 factice", "application/pdf")})
    assert r.status_code == 422 and "pas pu être lu" in r.json()["detail"]


def test_upload_mauvais_format() -> None:
    r = client.post("/upload", files={"fichier": ("notes.docx", b"x", "application/octet-stream")})
    assert r.status_code == 415


def test_get_course() -> None:
    r = client.get(f"/course/{COURSE_ID}")
    assert r.status_code == 200 and Course.model_validate(r.json()).nombre_slides == 2


def test_explain() -> None:
    r = client.get(f"/slide/{SLIDE_ID}/explain", params={"niveau": "debutant"})
    assert r.status_code == 200 and AgentResponse.model_validate(r.json()).agent == "explainer"


def test_ask() -> None:
    r = client.post(
        "/ask",
        json={
            "course_id": COURSE_ID,
            "slide_courante": 2,
            "question": "Que minimise-t-on ?",
            "niveau": "intermediaire",
            "langue": "fr",
        },
    )
    rep = AgentResponse.model_validate(r.json())
    assert r.status_code == 200 and "[Slide 2]" in rep.reponse and rep.sources[0].numero == 2


def test_quiz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.setenv("LLM_FAKE_REPONSE", json.dumps({"qcm": [{
        "question": "Que minimise-t-on ?", "choix": ["MSE", "MAE", "R2", "AUC"], "bonne_reponse": 0,
        "explication": "MSE.", "niveau_bloom": "memoriser", "slide": 2}]}))
    r = client.get("/quiz", params={"course_id": COURSE_ID, "slide": 2})
    assert r.status_code == 200 and len([QCM.model_validate(q) for q in r.json()]) > 0


def test_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.delenv("LLM_FAKE_REPONSE", raising=False)
    r = client.get("/resources", params={"slide_id": SLIDE_ID})
    assert r.status_code == 200 and len([Ressource.model_validate(x) for x in r.json()]) > 0
