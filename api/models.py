"""Modèles propres à l'API, absents de ``schemas/models.py``.

Les modèles partagés (Course, AgentResponse, Source…) restent dans ``schemas/`` ;
ce module ne définit que ce qui manque au contrat commun.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas.models import COURSE_ID_PATTERN, Langue, Niveau, Source


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AskRequest(_Base):
    """Corps de ``POST /ask``."""

    course_id: str = Field(pattern=COURSE_ID_PATTERN)
    slide_courante: int = Field(ge=1)
    question: str = Field(min_length=1)
    niveau: Niveau = "intermediaire"
    langue: Langue = "fr"


class QCM(_Base):
    """Question à choix multiples renvoyée par ``GET /quiz``."""

    question: str
    choix: list[str] = Field(min_length=2)
    bonne_reponse: int = Field(ge=0, description="Index de la bonne réponse dans ``choix``")
    explication: str = ""
    source: Source


class Ressource(_Base):
    """Ressource externe renvoyée par ``GET /resources``."""

    titre: str
    url: str
    type: Literal["video", "article", "cours", "exercice", "documentation"]
    langue: Langue = "fr"
    description: str = ""


__all__ = ["QCM", "AskRequest", "Ressource"]
