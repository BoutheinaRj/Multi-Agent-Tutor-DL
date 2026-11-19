"""Tests du moteur LLM local (A0) : backend fake et erreurs, sans modèle téléchargé."""

from __future__ import annotations

import json
from typing import Literal

import pytest
from pydantic import BaseModel, Field

from agents import llm
from api.models import QCM


@pytest.fixture(autouse=True)
def _isoler(monkeypatch: pytest.MonkeyPatch) -> None:
    for cle in ("LLM_BACKEND", "LLM_MODEL_PATH", "LLM_N_CTX", "LLM_MODEL", "LLM_FAKE_REPONSE"):
        monkeypatch.delenv(cle, raising=False)
    llm.reinitialiser()


class _Choix(BaseModel):
    index: int = Field(ge=1)
    justification: str = Field(min_length=10)
    niveau: Literal["debutant", "avance"]


class _Selection(BaseModel):
    choix: list[_Choix] = Field(min_length=2)
    commentaire: str | None = None


# --------------------------------------------------------------------------- backend fake


def test_fake_est_configure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    assert llm.est_configure()


def test_fake_structure_respecte_le_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    reponse = llm.generer_structure("s", "p", _Selection)
    assert isinstance(reponse, _Selection)
    assert len(reponse.choix) == 2
    assert reponse.choix[0].index == 1 and reponse.choix[0].niveau == "debutant"
    assert len(reponse.choix[0].justification) >= 10


def test_fake_structure_modele_imbrique(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    qcm = llm.generer_structure("s", "p", QCM)
    assert len(qcm.choix) >= 2 and qcm.bonne_reponse == 0


def test_fake_deterministe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    assert llm.generer_structure("s", "p", QCM) == llm.generer_structure("autre", "chose", QCM)
    assert llm.generer_texte("s", "bonjour") == llm.generer_texte("s", "bonjour")


def test_fake_reponse_imposee(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    donnees = {"choix": [{"index": 3, "justification": "Explique la MSE.", "niveau": "avance"}] * 2}
    monkeypatch.setenv("LLM_FAKE_REPONSE", json.dumps(donnees))
    reponse = llm.generer_structure("s", "p", _Selection)
    assert reponse.choix[0].index == 3


def test_fake_reponse_imposee_invalide(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.setenv("LLM_FAKE_REPONSE", '{"choix": []}')
    with pytest.raises(llm.LLMIndisponible):
        llm.generer_structure("s", "p", _Selection)


def test_fake_texte(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    assert "MSE" in llm.generer_texte("s", "Explique la MSE", max_tokens=50)


# --------------------------------------------------------------------------- erreurs et configuration


def test_modele_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "llamacpp")
    monkeypatch.setenv("LLM_MODEL_PATH", "models/__absent__.gguf")
    assert not llm.est_configure()
    with pytest.raises(llm.LLMIndisponible, match="introuvable"):
        llm.generer_structure("s", "p", QCM)
    with pytest.raises(llm.LLMIndisponible):
        llm.generer_texte("s", "p")


def test_backend_inconnu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "anthropic")
    assert not llm.est_configure()
    with pytest.raises(llm.LLMIndisponible, match="inconnu"):
        llm.generer_texte("s", "p")


def test_chemin_relatif_part_de_la_racine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODEL_PATH", "models/x.gguf")
    assert llm.chemin_modele() == llm.RACINE / "models" / "x.gguf"


def test_hors_ligne_force() -> None:
    import os

    assert os.environ["HF_HUB_OFFLINE"] == "1"


# --------------------------------------------------------------------------- validation et nouvelle tentative


class _FauxLlama:
    """Imite ``llama_cpp.Llama.create_chat_completion`` avec des réponses préparées."""

    def __init__(self, reponses: list[str]) -> None:
        self.reponses = reponses
        self.appels: list[dict] = []

    def create_chat_completion(self, **kwargs: object) -> dict:
        self.appels.append(kwargs)
        return {"choices": [{"message": {"content": self.reponses.pop(0)}}]}


def test_nouvelle_tentative_si_invalide(monkeypatch: pytest.MonkeyPatch) -> None:
    faux = _FauxLlama(['{"choix": []}', json.dumps(
        {"choix": [{"index": 1, "justification": "Assez longue.", "niveau": "avance"}] * 2})])
    monkeypatch.setattr(llm, "_llama", lambda: faux)
    reponse = llm.generer_structure("s", "p", _Selection, max_tokens=64)
    assert len(reponse.choix) == 2
    assert len(faux.appels) == 2
    assert faux.appels[0]["response_format"]["type"] == "json_object"
    assert faux.appels[0]["response_format"]["schema"] == _Selection.model_json_schema()
    assert faux.appels[0]["max_tokens"] == 64
    assert "invalide" in faux.appels[1]["messages"][-1]["content"]


def test_echec_apres_deux_tentatives(monkeypatch: pytest.MonkeyPatch) -> None:
    faux = _FauxLlama(["pas du json", '{"choix": []}'])
    monkeypatch.setattr(llm, "_llama", lambda: faux)
    with pytest.raises(llm.LLMIndisponible, match="2 tentatives"):
        llm.generer_structure("s", "p", _Selection)


def test_texte_llamacpp_sans_contrainte(monkeypatch: pytest.MonkeyPatch) -> None:
    faux = _FauxLlama(["  Bonjour.  "])
    monkeypatch.setattr(llm, "_llama", lambda: faux)
    assert llm.generer_texte("s", "p") == "Bonjour."
    assert "response_format" not in faux.appels[0]
