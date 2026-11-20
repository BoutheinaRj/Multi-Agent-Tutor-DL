"""Tests du tuteur complet (O5) : modèles légers, LLM fake, aucun réseau, aucun modèle chargé."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from agents import explainer as ex
from agents import quiz as qz
from agents.tuteur import MotsClesReranker, Tuteur, modeles_par_defaut
from schemas import Course

EXEMPLE = Path(__file__).resolve().parent.parent / "schemas" / "exemples" / "exemple_cours.json"


@pytest.fixture(autouse=True)
def _isoler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "fake")
    monkeypatch.delenv("LLM_FAKE_REPONSE", raising=False)
    monkeypatch.setattr(qz, "_recherche_rag", lambda: None)
    monkeypatch.setattr(ex, "_prerequis_h3", lambda: None)
    connect = socket.socket.connect

    def _local_seulement(sock: socket.socket, adresse: Any, *args: Any) -> Any:
        hote = adresse[0] if isinstance(adresse, tuple) else adresse
        if hote not in ("127.0.0.1", "::1", "localhost"):
            raise AssertionError(f"appel réseau inattendu vers {adresse!r}")
        return connect(sock, adresse, *args)

    monkeypatch.setattr(socket.socket, "connect", _local_seulement)


@pytest.fixture
def tuteur() -> Tuteur:
    t = Tuteur("leger")
    t.ajouter_cours(Course.model_validate(json.loads(EXEMPLE.read_text(encoding="utf-8"))))
    return t


# --------------------------------------------------------------------------- réglages


def test_modeles_par_defaut_suit_l_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TUTEUR_MODELES", "leger")
    assert modeles_par_defaut() == "leger"
    monkeypatch.setenv("TUTEUR_MODELES", "complet")
    assert modeles_par_defaut() == "complet"


def test_reranker_leger_ignore_les_mots_vides() -> None:
    r = MotsClesReranker()
    slide = "Qui minimise la fonction de coût ? On minimise l'erreur quadratique moyenne."
    hors_sujet, dans_le_cours = r.scorer("Qui a gagné la coupe du monde ?", [slide])[0], \
        r.scorer("Que minimise la fonction de coût ?", [slide])[0]
    assert hors_sujet == 0.0 and dans_le_cours == 1.0


# --------------------------------------------------------------------------- de bout en bout


def test_explication_passe_par_le_critic(tuteur: Tuteur) -> None:
    rep = tuteur.expliquer("ml_regression_lineaire_fr", 2, niveau="debutant")
    assert rep.agent == "explainer"
    assert rep.reponse.startswith("**Idée clé**") and "[Slide 2]" in rep.reponse
    assert rep.score_fidelite is not None  # le Critic a noté la réponse
    assert [s.numero for s in rep.sources][0] == 2


def test_question_du_cours_sourcee(tuteur: Tuteur) -> None:
    rep = tuteur.demander("ml_regression_lineaire_fr", 2, "Que minimise la fonction de coût ?")
    assert rep.agent == "qa" and rep.sources and rep.sources[0].numero == 2


def test_question_hors_cours_refusee(tuteur: Tuteur) -> None:
    rep = tuteur.demander("ml_regression_lineaire_fr", 2, "Qui a gagné la coupe du monde 2018 ?")
    assert rep.agent == "qa" and "pas dans le cours" in rep.reponse


def test_demande_de_quiz_routee_vers_le_quiz_verifie(tuteur: Tuteur) -> None:
    rep = tuteur.demander("ml_regression_lineaire_fr", 2, "Fais-moi un quiz")
    assert rep.agent == "quiz"


def test_ingestion_puis_question(tmp_path: Path) -> None:
    import pymupdf

    doc = pymupdf.open()
    for titre, texte in [("Les arbres de decision", "Un arbre partage les donnees selon des seuils."),
                         ("Elagage", "L'elagage retire les branches qui surapprennent.")]:
        page = doc.new_page()
        page.insert_text((72, 90), titre, fontsize=24)
        page.insert_text((72, 150), texte, fontsize=12)
    fichier = tmp_path / "arbres.pdf"
    doc.save(fichier)

    t = Tuteur("leger", dossier_sortie=tmp_path / "processed")
    cours = t.ingerer(fichier, rapide=True)
    assert cours.nombre_slides == 2 and cours.id in t.cours
    rep = t.demander(cours.id, 2, "Que retire l'elagage ?")
    assert rep.sources[0].numero == 2


# --------------------------------------------------------------------------- bug corrigé en intégration


def test_titre_pdf_garde_les_espaces_entre_les_mots() -> None:
    """PDF LaTeX/Beamer : chaque mot est un span, les espaces sont des spans à part."""
    from ingestion.parse import _titre_pdf

    def span(texte: str, taille: float) -> dict[str, Any]:
        return {"text": texte, "size": taille}

    titre = [span(m, 14.3) for m in ("Descente", " ", "de", " ", "gradient")]
    corps = [span("Algorithme", 10.0)]
    page = SimpleNamespace(
        rect=SimpleNamespace(y0=0, height=600),
        get_text=lambda _: {"blocks": [
            {"lines": [{"spans": titre, "bbox": (0, 40, 300, 60)}]},
            {"lines": [{"spans": corps, "bbox": (0, 300, 300, 320)} for _ in range(6)]},
        ]},
    )
    assert _titre_pdf(page) == "Descente de gradient"  # type: ignore[arg-type]
