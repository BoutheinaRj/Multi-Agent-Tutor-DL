"""Tests de bout en bout du squelette LangGraph (O1)."""

from __future__ import annotations

from typing import Any

import pytest

from agents.graph import classer_intention, construire_graphe, executer
from schemas import Source, TutorState


def _etat(**kwargs: Any) -> TutorState:
    return TutorState(course_id="ml_test_fr", slide_courante=3, **kwargs)


@pytest.mark.parametrize(
    ("question", "attendu"),
    [
        ("Explique-moi cette slide", "expliquer"),
        ("Can you explain the formula?", "expliquer"),
        ("Fais-moi un QCM sur ce chapitre", "quiz"),
        ("Test me with flashcards", "quiz"),
        ("Tu as une vidéo pour aller plus loin ?", "ressources"),
        ("Any further reading on transformers?", "ressources"),
        ("Quelle est la différence entre SGD et Adam ?", "question"),
        ("What is backpropagation?", "question"),
        ("Quel est le lien entre la perte et le gradient ?", "question"),
    ],
)
def test_classer_intention(question: str, attendu: str) -> None:
    assert classer_intention(question) == attendu


@pytest.mark.parametrize(
    ("question", "agent"),
    [
        ("Explique cette slide", "explainer"),
        ("Pourquoi le gradient est-il nul ici ?", "qa"),
        ("Un quiz stp", "quiz"),
        ("Des ressources sur ce sujet ?", "resources"),
    ],
)
def test_bout_en_bout_bouchons(question: str, agent: str) -> None:
    final = executer(_etat(question=question))
    assert final.reponse.startswith(f"[{agent}]")
    assert "[Slide 3]" in final.reponse
    assert final.sources == [Source(course_id="ml_test_fr", numero=3)]
    assert [m.role for m in final.historique] == ["utilisateur", "tuteur"]
    assert final.course_id == "ml_test_fr" and final.slide_courante == 3


def test_intention_imposee_par_api() -> None:
    final = executer(_etat(question="Un quiz stp", intention="expliquer"))
    assert final.intention == "expliquer"
    assert final.reponse.startswith("[explainer]")


def test_sans_question_on_explique() -> None:
    final = executer(_etat())
    assert final.intention == "expliquer"
    assert [m.role for m in final.historique] == ["tuteur"]


def test_brancher_un_agent() -> None:
    def agent_qa(state: TutorState) -> dict[str, Any]:
        return {"reponse": f"Vraie réponse à : {state.question}", "sources": []}

    graphe = construire_graphe({"question": agent_qa})
    final = executer(_etat(question="Pourquoi ?"), graphe)
    assert final.reponse == "Vraie réponse à : Pourquoi ?"
    autre = executer(_etat(question="Un quiz"), graphe)
    assert autre.reponse.startswith("[quiz]")


def test_intention_inconnue_refusee() -> None:
    with pytest.raises(ValueError):
        construire_graphe({"danse": lambda s: {}})  # type: ignore[dict-item]


def test_historique_conserve() -> None:
    premier = executer(_etat(question="Explique"))
    second = executer(premier.model_copy(update={"question": "Et ensuite ?", "intention": None}))
    assert len(second.historique) == 4
