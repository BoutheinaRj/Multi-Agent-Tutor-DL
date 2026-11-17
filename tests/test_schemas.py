"""Tests du schéma T0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas import Course, Slide, TutorState, est_course_id_valide, slide_id
from schemas.export import DOSSIER, generer

EXEMPLE = DOSSIER / "exemples" / "exemple_cours.json"


def _slide(numero: int, course_id: str = "ml_test_fr") -> Slide:
    return Slide(id=slide_id(course_id, numero), course_id=course_id, numero=numero)


def test_exemple_valide() -> None:
    cours = Course.model_validate_json(EXEMPLE.read_text(encoding="utf-8"))
    assert cours.nombre_slides == 2
    assert cours.slides[1].formules_latex


def test_slide_id_incoherent() -> None:
    with pytest.raises(ValidationError):
        Slide(id="ml_test_fr__s002", course_id="ml_test_fr", numero=1)


def test_champ_inconnu_refuse() -> None:
    with pytest.raises(ValidationError):
        Slide(id=slide_id("ml_test_fr", 1), course_id="ml_test_fr", numero=1, auteur="x")


def test_numerotation_discontinue() -> None:
    with pytest.raises(ValidationError):
        Course(
            id="ml_test_fr", titre="t", fichier_source="f.pdf", format="pdf", langue="fr",
            nombre_slides=2, slides=[_slide(1), _slide(3)],
        )


def test_nombre_slides_incoherent() -> None:
    with pytest.raises(ValidationError):
        Course(
            id="ml_test_fr", titre="t", fichier_source="f.pdf", format="pdf", langue="fr",
            nombre_slides=3, slides=[_slide(1), _slide(2)],
        )


def test_critic_max_deux_iterations() -> None:
    with pytest.raises(ValidationError):
        TutorState(course_id="ml_test_fr", slide_courante=1, iterations_critic=3)


@pytest.mark.parametrize(
    ("valeur", "attendu"),
    [("ml_regression_fr", True), ("ML_fr", False), ("cours-1", False), ("a__b", False)],
)
def test_course_id(valeur: str, attendu: bool) -> None:
    assert est_course_id_valide(valeur) is attendu


def test_json_schema_a_jour() -> None:
    """Les fichiers schemas/*.json doivent correspondre aux modèles (python -m schemas.export)."""
    for nom, contenu in generer().items():
        fichier = Path(DOSSIER / nom)
        assert fichier.exists(), f"{nom} manquant : lancer python -m schemas.export"
        assert json.loads(fichier.read_text(encoding="utf-8")) == json.loads(contenu), nom
