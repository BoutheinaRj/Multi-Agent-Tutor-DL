"""A2 — Agent Quiz : QCM et flashcards générés par le LLM local, sans aucune API externe.

1. Récupère le contenu du cours via ``recherche(course_id, requete, k)`` : RAG de Both
   (``rag/search.py``, B2) s'il existe, sinon bouchon local qui lit les slides du cours ;
2. un SEUL appel ``agents.llm.generer_structure`` par lot (schéma court, ``max_tokens`` serré :
   le LLM tourne sur CPU) ;
3. vérification Python des QCM (4 choix distincts, ``bonne_reponse`` dans 0..3, bonne réponse
   non dupliquée), rejet des QCM invalides, puis mélange des choix ;
4. sans LLM (``LLMIndisponible``) : flashcards titre → texte de la slide, quiz vide avec message.

Branchement dans le graphe (O1) :

    from agents.graph import construire_graphe
    from agents.quiz import quiz_agent

    graphe = construire_graphe({"quiz": quiz_agent})
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import random
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, create_model

from agents import llm
from agents.resources import mots_cles, normaliser
from api.models import QCM, Flashcard, NiveauBloom
from schemas import Chunk, Course, Message, SearchHit, Source, TutorState
from schemas.models import Langue

log = logging.getLogger(__name__)

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_PROCESSED = RACINE / "data" / "processed"
EXEMPLE_COURS = RACINE / "schemas" / "exemples" / "exemple_cours.json"
PROMPTS = RACINE / "prompts" / "quiz.md"

N_QCM_PAR_DEFAUT = 3
N_FLASHCARDS_PAR_DEFAUT = 5
N_MAX = 10
# Budget CPU : contexte et sortie courts.
MAX_CARACTERES_PAR_SLIDE = 700
MAX_CARACTERES_CONTEXTE = 2000
MAX_SLIDES_CONTEXTE = 4
TOKENS_BASE = 48
TOKENS_PAR_QCM = 230
TOKENS_PAR_FLASHCARD = 110
MAX_CARACTERES_EXTRAIT = 300

LANGUES_LISIBLES = {"fr": "français", "en": "anglais (English)", "ar": "arabe", "mixte": "français"}
NIVEAUX_BLOOM: tuple[NiveauBloom, ...] = ("memoriser", "comprendre", "appliquer", "analyser")

ChargerCours = Callable[[str], Course | None]
Recherche = Callable[[str, str, int], list[SearchHit]]


# --------------------------------------------------------------------------- cours disponibles

# Cours chargés par l'API (``api.main`` y branche ``COURS.get``), consultés en premier.
_SOURCES_COURS: list[ChargerCours] = []


def brancher_cours(source: ChargerCours) -> None:
    """Déclarer une source de cours prioritaire (p. ex. les cours chargés par l'API)."""
    if source not in _SOURCES_COURS:
        _SOURCES_COURS.append(source)


@lru_cache(maxsize=8)
def _lire_cours(chemin: str, _mtime: float) -> Course:
    return Course.model_validate(json.loads(Path(chemin).read_text(encoding="utf-8")))


def _cours_fichier(chemin: Path) -> Course | None:
    if not chemin.is_file():
        return None
    return _lire_cours(str(chemin), chemin.stat().st_mtime)


def charger_cours(course_id: str) -> Course | None:
    """Cours chargé par l'API, sinon ``data/processed/<id>/course.json``, sinon le cours d'exemple."""
    for source in _SOURCES_COURS:
        cours = source(course_id)
        if cours is not None:
            return cours
    cours = _cours_fichier(DOSSIER_PROCESSED / course_id / "course.json")
    if cours is not None:
        return cours
    exemple = _cours_fichier(EXEMPLE_COURS)
    return exemple if exemple is not None and exemple.id == course_id else None


# --------------------------------------------------------------------------- recherche (RAG ou bouchon)


def _chunk(cours: Course, numero: int) -> Chunk:
    s = cours.slides[numero - 1]
    morceaux = [s.texte, s.notes, *s.description_figures, *s.formules_latex]
    voisin = lambda i: cours.slides[i - 1].titre if 1 <= i <= cours.nombre_slides else ""  # noqa: E731
    return Chunk(
        id=s.id,
        course_id=cours.id,
        numero=s.numero,
        titre=s.titre,
        contenu="\n".join(m.strip() for m in morceaux if m and m.strip()),
        contexte_precedent=voisin(numero - 1),
        contexte_suivant=voisin(numero + 1),
        langue=cours.langue,
    )


def recherche_locale(course_id: str, requete: str, k: int) -> list[SearchHit]:
    """Bouchon du RAG : slides du cours triées par mots-clés communs avec la requête.

    TODO [B2] brancher rag.search : ce bouchon disparaît dès que ``rag/search.py`` existe.
    """
    cours = charger_cours(course_id)
    if cours is None or k <= 0:
        return []
    cles = mots_cles(requete)
    notes: list[tuple[float, int, Chunk]] = []
    for numero in range(1, cours.nombre_slides + 1):
        chunk = _chunk(cours, numero)
        if not (chunk.titre or chunk.contenu):
            continue
        commun = len(cles & mots_cles(f"{chunk.titre} {chunk.contenu}"))
        notes.append((commun / (len(cles) or 1), numero, chunk))
    notes.sort(key=lambda n: (-n[0], n[1]))
    return [SearchHit(chunk=c, score=sc) for sc, _, c in notes[:k]]


def _recherche_rag() -> Recherche | None:
    """La fonction de recherche de ``rag/search.py`` (B2) si le module existe."""
    if importlib.util.find_spec("rag") is None or importlib.util.find_spec("rag.search") is None:
        return None
    module = importlib.import_module("rag.search")
    fonction = getattr(module, "recherche", None) or getattr(module, "search", None)
    return fonction if callable(fonction) else None


def recherche(course_id: str, requete: str, k: int = MAX_SLIDES_CONTEXTE) -> list[SearchHit]:
    """Top-``k`` des slides du cours pour ``requete`` : RAG (B2) si présent, sinon bouchon local."""
    rag = _recherche_rag()
    if rag is not None:
        try:
            return list(rag(course_id, requete, k))
        except Exception as e:  # noqa: BLE001 - le RAG ne doit pas faire planter le quiz
            log.warning("rag.search a échoué, repli sur le bouchon local : %s", e)
    return recherche_locale(course_id, requete, k)


def contexte(course_id: str, slide: int | None, k: int = MAX_SLIDES_CONTEXTE) -> list[Chunk]:
    """Slides sur lesquelles porte le lot : la slide demandée, sinon les ``k`` plus pertinentes."""
    cours = charger_cours(course_id)
    if slide is not None:
        if cours is not None and 1 <= slide <= cours.nombre_slides:
            s = cours.slides[slide - 1]
            hits = recherche(course_id, f"{s.titre} {s.texte}", k)
        else:
            hits = recherche(course_id, "", max(k, slide))
        trouves = [h.chunk for h in hits if h.chunk.numero == slide]
        if trouves:
            return trouves[:1]
        return [_chunk(cours, slide)] if cours is not None and 1 <= slide <= cours.nombre_slides else []
    requete = f"{cours.titre} {cours.resume}" if cours is not None else ""
    return [h.chunk for h in recherche(course_id, requete, k)]


# --------------------------------------------------------------------------- prompts


@lru_cache(maxsize=2)
def _lire_prompts(chemin: str, _mtime: float) -> dict[str, str]:
    sections: dict[str, str] = {}
    for bloc in re.split(r"^## ", Path(chemin).read_text(encoding="utf-8"), flags=re.M)[1:]:
        titre, _, corps = bloc.partition("\n")
        sections[normaliser(titre)] = corps.strip()
    return sections


PROMPT_SECOURS = (
    "Tu rédiges du matériel de révision à partir de slides de cours. Appuie-toi uniquement "
    "sur les slides fournies et rédige dans la langue demandée."
)


def prompt_systeme(section: str) -> str:
    """Section ``## <section>`` de ``prompts/quiz.md`` (prompt de secours si absente)."""
    if PROMPTS.is_file():
        texte = _lire_prompts(str(PROMPTS), PROMPTS.stat().st_mtime).get(normaliser(section))
        if texte:
            return texte
    log.warning("section %r absente de %s, prompt de secours", section, PROMPTS)
    return PROMPT_SECOURS


def _bloc_slides(chunks: list[Chunk]) -> str:
    lignes: list[str] = []
    reste = MAX_CARACTERES_CONTEXTE
    for c in chunks:
        corps = c.contenu[: min(MAX_CARACTERES_PAR_SLIDE, max(reste, 0))]
        reste -= len(corps)
        lignes.append(f"[Slide {c.numero}] {c.titre}\n{corps}".strip())
        if reste <= 0:
            break
    return "\n\n".join(lignes)


def _prompt_lot(chunks: list[Chunk], n: int, langue: Langue, quoi: str, bloom: str = "") -> str:
    lignes = [
        f"Langue : {LANGUES_LISIBLES.get(langue, langue)}.",
        f"Nombre de {quoi} : {n}.",
    ]
    if bloom:
        lignes.append(bloom)
    lignes += ["", "Slides :", _bloc_slides(chunks)]
    return "\n".join(lignes)


# --------------------------------------------------------------------------- schémas courts pour le LLM


# Bornes de longueur : imposées par la grammaire llama.cpp, elles évitent qu'une réponse
# trop bavarde dépasse ``max_tokens`` (JSON tronqué = nouvel essai, donc deux fois plus lent).
# Elles ne figurent que dans le schéma JSON : Pydantic ne rejette pas un texte trop long.
MAX_QUESTION, MAX_CHOIX, MAX_EXPLICATION = 160, 80, 160
MAX_RECTO, MAX_VERSO = 100, 200


def _texte(max_len: int, **kwargs: Any) -> Any:
    return Field(json_schema_extra={"maxLength": max_len}, **kwargs)


class _QCMBrut(BaseModel):
    question: str = _texte(MAX_QUESTION)
    choix: list[str] = Field(min_length=4, max_length=4, json_schema_extra={
        "items": {"type": "string", "maxLength": MAX_CHOIX}})
    # Pas de bornes ici (la grammaire llama.cpp ne les applique pas) : vérification Python.
    bonne_reponse: int = Field(description="Index 0 à 3 de la bonne réponse")
    explication: str = _texte(MAX_EXPLICATION)
    niveau_bloom: NiveauBloom
    slide: int


class _FlashcardBrute(BaseModel):
    recto: str = _texte(MAX_RECTO)
    verso: str = _texte(MAX_VERSO)
    slide: int


@lru_cache(maxsize=2 * N_MAX)
def _schema_lot(nom: str, n: int) -> type[BaseModel]:
    """Schéma d'un lot de ``n`` éléments au plus : le modèle s'arrête au bon nombre.

    ``maxItems`` n'est que dans le schéma JSON (grammaire llama.cpp) : un lot trop long venu
    d'un backend non contraint est tronqué en Python plutôt que rejeté en entier.
    """
    element: type[BaseModel] = _QCMBrut if nom == "qcm" else _FlashcardBrute
    champ = Field(min_length=1, json_schema_extra={"maxItems": n})
    return create_model(f"_Lot_{nom}_{n}", **{nom: (list[element], champ)})  # type: ignore[call-overload]


# Le modèle écrit parfois du LaTeX non échappé : « \theta » devient tabulation + « heta ».
_LATEX_CASSE = str.maketrans({"\t": "\\t", "\b": "\\b", "\f": "\\f", "\r": "\\r"})


def nettoyer(texte: str) -> str:
    return texte.translate(_LATEX_CASSE).strip()


# --------------------------------------------------------------------------- vérification et mélange


def valider_qcm(brut: _QCMBrut) -> str | None:
    """Motif de rejet d'un QCM brut, ou ``None`` s'il est valide."""
    if not brut.question.strip():
        return "question vide"
    choix = [c.strip() for c in brut.choix]
    if len(choix) != 4:
        return f"{len(choix)} choix au lieu de 4"
    if any(not c for c in choix):
        return "choix vide"
    if not 0 <= brut.bonne_reponse <= 3:
        return f"bonne_reponse hors limites : {brut.bonne_reponse}"
    normalises = [normaliser(c) or c.lower() for c in choix]
    if normalises.count(normalises[brut.bonne_reponse]) > 1:
        return "bonne réponse dupliquée"
    if len(set(normalises)) != 4:
        return "choix non distincts"
    return None


def melanger(qcm: QCM, rng: random.Random) -> QCM:
    """Mélanger les choix et mettre à jour ``bonne_reponse``."""
    ordre = list(range(len(qcm.choix)))
    rng.shuffle(ordre)
    return qcm.model_copy(update={
        "choix": [qcm.choix[i] for i in ordre],
        "bonne_reponse": ordre.index(qcm.bonne_reponse),
    })


def _source(chunks: list[Chunk], numero: int) -> Source:
    par_numero = {c.numero: c for c in chunks}
    chunk = par_numero.get(numero) or chunks[0]
    return Source(course_id=chunk.course_id, numero=chunk.numero,
                  extrait=chunk.contenu[:MAX_CARACTERES_EXTRAIT])


# --------------------------------------------------------------------------- génération


@dataclass
class ResultatQuiz:
    """QCM retenus et, s'il n'y en a aucun, le message à afficher."""

    qcm: list[QCM]
    message: str = ""


def _langue(course_id: str, langue: Langue | None) -> Langue:
    if langue is not None:
        return langue
    cours = charger_cours(course_id)
    return cours.langue if cours is not None and cours.langue != "mixte" else "fr"


def _borner(n: int) -> int:
    return max(1, min(int(n), N_MAX))


def generer_quiz_detaille(
    course_id: str,
    slide: int | None = None,
    n: int = N_QCM_PAR_DEFAUT,
    niveau_bloom: NiveauBloom | None = None,
    *,
    langue: Langue | None = None,
    rng: random.Random | None = None,
) -> ResultatQuiz:
    """Comme ``generer_quiz``, avec le message expliquant un quiz vide."""
    n = _borner(n)
    chunks = contexte(course_id, slide)
    if not chunks:
        cible = f"la slide {slide} de " if slide is not None else ""
        return ResultatQuiz([], f"Aucun contenu trouvé pour {cible}{course_id} : quiz impossible.")
    bloom = (f"Niveau de Bloom imposé : {niveau_bloom}." if niveau_bloom
             else f"Varie les niveaux de Bloom ({', '.join(NIVEAUX_BLOOM)}).")
    try:
        lot = llm.generer_structure(
            prompt_systeme("QCM"),
            _prompt_lot(chunks, n, _langue(course_id, langue), "QCM", bloom),
            _schema_lot("qcm", n),
            max_tokens=TOKENS_BASE + TOKENS_PAR_QCM * n,
        )
    except llm.LLMIndisponible as e:
        log.warning("quiz : LLM local indisponible : %s", e)
        return ResultatQuiz([], f"Quiz indisponible : le LLM local n'a pas pu répondre ({e}).")

    rng = rng or random.Random()
    retenus: list[QCM] = []
    vues: set[str] = set()
    for brut in lot.qcm:  # type: ignore[attr-defined]
        motif = valider_qcm(brut)
        if motif is None and normaliser(brut.question) in vues:
            motif = "question en double"
        if motif is not None:
            log.info("QCM rejeté (%s) : %s", motif, brut.question[:80])
            continue
        vues.add(normaliser(brut.question))
        qcm = QCM(
            question=nettoyer(brut.question),
            choix=[nettoyer(c) for c in brut.choix],
            bonne_reponse=brut.bonne_reponse,
            explication=nettoyer(brut.explication),
            niveau_bloom=niveau_bloom or brut.niveau_bloom,
            source=_source(chunks, slide if slide is not None else brut.slide),
        )
        retenus.append(melanger(qcm, rng))
        if len(retenus) == n:
            break
    if not retenus:
        return ResultatQuiz([], "Quiz indisponible : aucun QCM généré n'a passé la vérification.")
    return ResultatQuiz(retenus)


def generer_quiz(
    course_id: str,
    slide: int | None = None,
    n: int = N_QCM_PAR_DEFAUT,
    niveau_bloom: NiveauBloom | None = None,
    *,
    langue: Langue | None = None,
    rng: random.Random | None = None,
) -> list[QCM]:
    """Au plus ``n`` QCM vérifiés sur la slide (ou le cours), en un seul appel LLM ; ``[]`` sinon."""
    return generer_quiz_detaille(course_id, slide, n, niveau_bloom, langue=langue, rng=rng).qcm


def flashcards_sans_llm(chunks: list[Chunk], n: int) -> list[Flashcard]:
    """Repli sans LLM : une carte par slide, titre → texte de la slide."""
    cartes: list[Flashcard] = []
    for c in chunks:
        verso = c.contenu.strip()
        if not verso:
            continue
        recto = c.titre.strip() or f"Slide {c.numero}"
        cartes.append(Flashcard(recto=recto, verso=verso[:MAX_CARACTERES_PAR_SLIDE],
                                source=_source(chunks, c.numero)))
    return cartes[:n]


def generer_flashcards(
    course_id: str,
    slide: int | None = None,
    n: int = N_FLASHCARDS_PAR_DEFAUT,
    *,
    langue: Langue | None = None,
) -> list[Flashcard]:
    """Au plus ``n`` flashcards sur la slide (ou le cours), en un seul appel LLM ; repli sans LLM."""
    n = _borner(n)
    chunks = contexte(course_id, slide)
    if not chunks:
        return []
    try:
        lot = llm.generer_structure(
            prompt_systeme("Flashcards"),
            _prompt_lot(chunks, n, _langue(course_id, langue), "flashcards"),
            _schema_lot("cartes", n),
            max_tokens=TOKENS_BASE + TOKENS_PAR_FLASHCARD * n,
        )
    except llm.LLMIndisponible as e:
        log.warning("flashcards : LLM local indisponible, repli titre → texte : %s", e)
        return flashcards_sans_llm(chunks, n)
    cartes: list[Flashcard] = []
    vues: set[str] = set()
    for brute in lot.cartes:  # type: ignore[attr-defined]
        recto, verso = nettoyer(brute.recto), nettoyer(brute.verso)
        if not recto or not verso or normaliser(recto) in vues:
            continue
        vues.add(normaliser(recto))
        cartes.append(Flashcard(recto=recto, verso=verso,
                                source=_source(chunks, slide if slide is not None else brute.slide)))
    return cartes[:n] or flashcards_sans_llm(chunks, n)


# --------------------------------------------------------------------------- agent


LETTRES = "ABCD"


def formater_quiz(resultat: ResultatQuiz) -> str:
    if not resultat.qcm:
        return resultat.message
    lignes: list[str] = []
    for i, q in enumerate(resultat.qcm, 1):
        lignes.append(f"{i}. {q.question} [Slide {q.source.numero}]")
        lignes += [f"   {LETTRES[j]}. {c}" for j, c in enumerate(q.choix)]
    lignes.append("")
    lignes.append("Réponses :")
    for i, q in enumerate(resultat.qcm, 1):
        lignes.append(f"{i}. {LETTRES[q.bonne_reponse]} — {q.explication} [Slide {q.source.numero}]")
    return "\n".join(lignes)


def formater_flashcards(cartes: list[Flashcard], numero: int) -> str:
    if not cartes:
        return f"Aucune flashcard n'a pu être créée pour la slide {numero} [Slide {numero}]."
    return "\n".join(f"- {c.recto} → {c.verso} [Slide {c.source.numero}]" for c in cartes)


def veut_flashcards(question: str) -> bool:
    return any(m in normaliser(question) for m in ("flashcard", "flash card", "carte", "fiche"))


def quiz_agent(state: TutorState) -> dict[str, Any]:
    """Nœud LangGraph ``quiz`` : même signature et mêmes champs que les bouchons d'O1."""
    if veut_flashcards(state.question):
        cartes = generer_flashcards(state.course_id, state.slide_courante, langue=state.langue_reponse)
        reponse = formater_flashcards(cartes, state.slide_courante)
        sources = [c.source for c in cartes]
    else:
        resultat = generer_quiz_detaille(state.course_id, state.slide_courante,
                                         langue=state.langue_reponse)
        reponse = formater_quiz(resultat)
        sources = [q.source for q in resultat.qcm]
    uniques = list({s.numero: s for s in sources}.values()) or [
        Source(course_id=state.course_id, numero=state.slide_courante)
    ]
    historique = list(state.historique)
    if state.question:
        historique.append(Message(role="utilisateur", contenu=state.question))
    historique.append(Message(role="tuteur", contenu=reponse))
    return {"reponse": reponse, "sources": uniques, "historique": historique}


__all__ = [
    "ResultatQuiz",
    "brancher_cours",
    "charger_cours",
    "contexte",
    "flashcards_sans_llm",
    "generer_flashcards",
    "generer_quiz",
    "generer_quiz_detaille",
    "melanger",
    "quiz_agent",
    "recherche",
    "recherche_locale",
    "valider_qcm",
]
