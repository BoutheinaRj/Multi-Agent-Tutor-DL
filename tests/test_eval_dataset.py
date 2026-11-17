"""Validation du jeu d'évaluation C2 (eval/dataset.json)."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from eval.schema import REPONSE_HORS_COURS, QuestionEval, charger

RACINE = Path(__file__).resolve().parents[1]
DATASET = RACINE / "eval" / "dataset.json"
CORPUS = RACINE / "data" / "corpus"


def _slides_par_cours() -> dict[str, int]:
    """Nombre de slides de chaque cours, d'après les inventaires du corpus."""
    nombres: dict[str, int] = {}
    for inv in CORPUS.glob("inventaire_*.csv"):
        with open(inv, encoding="utf-8") as f:
            for ligne in csv.DictReader(f):
                nombres[Path(ligne["fichier"]).stem] = int(ligne["nombre_slides"])
    return nombres


def test_dataset_valide() -> None:
    jeu = charger(DATASET)
    assert jeu.questions


def test_cours_et_slides_existent() -> None:
    nombres = _slides_par_cours()
    for q in charger(DATASET).questions:
        assert q.course_id in nombres, f"{q.id} : cours absent des inventaires"
        assert all(n <= nombres[q.course_id] for n in q.slides), f"{q.id} : slide hors du cours"


def test_hors_cours_refus() -> None:
    for q in charger(DATASET).questions:
        if q.type == "hors_cours":
            assert q.reponse_reference == REPONSE_HORS_COURS


def test_types_varies_par_cours() -> None:
    """Chaque cours doit mélanger les 4 types de questions (démarche C2)."""
    par_cours: dict[str, Counter[str]] = {}
    for q in charger(DATASET).questions:
        par_cours.setdefault(q.course_id, Counter())[q.type] += 1
    for cours, types in par_cours.items():
        assert set(types) == {"factuelle", "comprehension", "figure", "hors_cours"}, cours


@pytest.mark.parametrize(
    "champs",
    [
        {"type": "hors_cours", "slides": [2]},
        {"type": "factuelle", "slides": []},
        {"id": "autre_cours__q01"},
        {"relu_par": "ons"},
    ],
)
def test_questions_invalides(champs: dict[str, object]) -> None:
    base: dict[str, object] = {
        "id": "ml_x_fr__q01", "course_id": "ml_x_fr", "auteur": "ons", "type": "factuelle",
        "langue": "fr", "question": "Question ?", "reponse_reference": "Réponse.", "slides": [1],
    }
    with pytest.raises(ValidationError):
        QuestionEval.model_validate({**base, **champs})
