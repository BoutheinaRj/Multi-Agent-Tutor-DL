"""Générer les JSON Schema (slide.json, course.json, chunk.json) à partir des modèles.

Usage : ``python -m schemas.export`` depuis la racine du dépôt.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from schemas.models import Chunk, Course, Slide, TutorState

DOSSIER = Path(__file__).resolve().parent
CIBLES: dict[str, type[BaseModel]] = {
    "slide.json": Slide,
    "course.json": Course,
    "chunk.json": Chunk,
    "tutor_state.json": TutorState,
}


def generer() -> dict[str, str]:
    """Renvoyer le contenu JSON de chaque schéma, indexé par nom de fichier."""
    return {
        nom: json.dumps(modele.model_json_schema(), indent=2, ensure_ascii=False) + "\n"
        for nom, modele in CIBLES.items()
    }


def main() -> None:
    """Écrire les schémas dans le dossier ``schemas/``."""
    for nom, contenu in generer().items():
        (DOSSIER / nom).write_text(contenu, encoding="utf-8")
        print(f"écrit : schemas/{nom}")


if __name__ == "__main__":
    main()
