"""Tests de l'API factice (A1) : une assertion par route."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from api.models import QCM, Ressource
from schemas import AgentResponse, Course

client = TestClient(app)

COURSE_ID = "ml_regression_lineaire_fr"
SLIDE_ID = f"{COURSE_ID}__s002"


def test_upload() -> None:
    r = client.post(
        "/upload",
        files={"fichier": ("cours.pdf", b"%PDF-1.4 factice", "application/pdf")},
    )
    assert r.status_code == 200 and Course.model_validate(r.json()).id == COURSE_ID


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


def test_quiz() -> None:
    r = client.get("/quiz", params={"course_id": COURSE_ID, "slide": 2})
    assert r.status_code == 200 and len([QCM.model_validate(q) for q in r.json()]) > 0


def test_resources() -> None:
    r = client.get("/resources", params={"slide_id": SLIDE_ID})
    assert r.status_code == 200 and len([Ressource.model_validate(x) for x in r.json()]) > 0
