"""C2 — Format du jeu d'évaluation (``eval/dataset.json``).

Chaque entrée est une question sur un cours du corpus, avec sa réponse de référence
et les slides qui la justifient. Le benchmark B4 (RAGAS) s'appuie sur ce format.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.models import COURSE_ID_PATTERN

TypeQuestion = Literal["factuelle", "comprehension", "figure", "hors_cours"]
Membre = Literal["ons", "both"]

# Réponse attendue de l'agent pour une question hors cours (refus, B3).
REPONSE_HORS_COURS = "L'information n'est pas dans le cours."


class QuestionEval(BaseModel):
    """Une question du jeu d'évaluation."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_]+__q\d{2}$", description="<course_id>__qNN")
    course_id: str = Field(pattern=COURSE_ID_PATTERN)
    auteur: Membre
    type: TypeQuestion
    langue: Literal["fr", "en"]
    question: str = Field(min_length=5)
    reponse_reference: str = Field(min_length=1)
    slides: list[int] = Field(default_factory=list, description="Numéros des slides sources (vide si hors cours)")
    relu_par: Membre | None = Field(default=None, description="Relecture croisée Ons ↔ Both")

    @model_validator(mode="after")
    def _verifier(self) -> QuestionEval:
        """Contrôler l'id, les slides et le cas hors cours."""
        if not self.id.startswith(f"{self.course_id}__q"):
            raise ValueError(f"id {self.id!r} ne commence pas par {self.course_id}__q")
        if self.type == "hors_cours":
            if self.slides:
                raise ValueError("une question hors cours n'a pas de slide source")
        elif not self.slides:
            raise ValueError("une question sur le cours doit citer au moins une slide")
        if any(n < 1 for n in self.slides):
            raise ValueError("numéro de slide < 1")
        if self.relu_par is not None and self.relu_par == self.auteur:
            raise ValueError("la relecture doit être faite par l'autre membre")
        return self


class JeuEvaluation(BaseModel):
    """Le fichier ``eval/dataset.json`` complet."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    questions: list[QuestionEval]

    @model_validator(mode="after")
    def _ids_uniques(self) -> JeuEvaluation:
        """Refuser deux questions avec le même id."""
        ids = [q.id for q in self.questions]
        doublons = {i for i in ids if ids.count(i) > 1}
        if doublons:
            raise ValueError(f"ids en double : {sorted(doublons)}")
        return self


def charger(chemin: Path) -> JeuEvaluation:
    """Charger et valider un jeu d'évaluation."""
    return JeuEvaluation.model_validate(json.loads(chemin.read_text(encoding="utf-8")))
