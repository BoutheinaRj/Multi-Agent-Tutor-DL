"""O5 — Le tuteur complet : ingestion (Ghayth), RAG (Both), agents (Ons, Both, Ali) et Critic.

Un seul objet relie tout ce que l'équipe a construit :

    PPTX / PDF ──▶ ingestion.ingest (H1 → H2 → H3) ──▶ data/processed/<id>/course.json
                                                  └──▶ rag.index (Qdrant, B1-B2)
    question ──▶ graphe LangGraph (O1)
                   router ──▶ explainer (O2) | qa (B3) ──▶ critic (O3) ──▶ réponse
                          └─▶ quiz vérifié (A2 + O3) | resources (A4)

Deux jeux de modèles, choisis par ``TUTEUR_MODELES`` (``.env``) :

- ``complet`` : bge-m3 + bge-reranker-v2-m3 dans ``qdrant_storage/`` (modèles téléchargés une
  fois, ~3 Go), le LLM local d'A0 (``LLM_BACKEND``) ;
- ``leger`` : embeddings par hachage et reranker par mots communs, en mémoire, sans aucun
  modèle : démarre en une seconde, pour les tests et la démo sans GPU.

Par défaut : ``complet`` si ``sentence-transformers`` est installé, sinon ``leger``.
Aucune API externe : tout tourne sur la machine (règle v2).

Utilisation :

    from agents.tuteur import Tuteur
    tuteur = Tuteur()
    cours = tuteur.ingerer("data/corpus/fr/ml/ml_gradient_stochastique_esprit_fr.pdf")
    tuteur.expliquer(cours.id, 3, niveau="debutant")
    tuteur.demander(cours.id, 3, "Pourquoi le pas doit-il décroître ?")
"""

from __future__ import annotations

import importlib.util
import logging
import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from agents import quiz as qz
from agents.critic import critic_agent, quiz_verifie_agent
from agents.explainer import explainer_agent
from agents.graph import construire_graphe, executer
from agents.qa import AgentQA
from agents.resources import resources_agent
from schemas import AgentResponse, Course, TutorState
from schemas.models import Intention, Langue, Niveau

log = logging.getLogger(__name__)

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_PROCESSED = RACINE / "data" / "processed"
DOSSIER_QDRANT = RACINE / "qdrant_storage"

Modeles = Literal["complet", "leger"]
SEUIL_QA_LEGER = float(os.getenv("QA_SEUIL_LEGER", "0.5"))
NOEUD_AGENT: dict[Intention, Any] = {
    "expliquer": "explainer",
    "question": "qa",
    "quiz": "quiz",
    "ressources": "resources",
}


def modeles_par_defaut() -> Modeles:
    """``TUTEUR_MODELES`` s'il est défini, sinon ``complet`` si les modèles du RAG sont installables."""
    choix = os.getenv("TUTEUR_MODELES", "").strip().lower()
    if choix in ("complet", "leger"):
        return choix  # type: ignore[return-value]
    return "complet" if importlib.util.find_spec("sentence_transformers") else "leger"


def construire_recherche(modeles: Modeles, chemin_qdrant: Path | None = None) -> Any:
    """La recherche de B1-B2 : hybride (dense + BM25) puis reranker, filtrée par cours."""
    from rag.rerank import RechercheReranked
    from rag.search import RechercheHybride
    from rag.store import VectorStore

    if modeles == "complet":
        from rag.rerank import BgeReranker
        from rag.store import BgeM3Embedder

        store = VectorStore(BgeM3Embedder(), chemin=str(chemin_qdrant or DOSSIER_QDRANT))
        return RechercheReranked(RechercheHybride(store), BgeReranker())

    from rag.store import HashEmbedder

    store = VectorStore(HashEmbedder(), collection="slides_hash")  # en mémoire
    return RechercheReranked(RechercheHybride(store), MotsClesReranker())


class MotsClesReranker:
    """Reranker léger, sans modèle : part des mots-clés de la question (mots vides retirés,
    pluriels ramenés au singulier) présents dans la slide. Score entre 0 et 1, comme bge-reranker.

    Sans retirer les mots vides (« qui », « la », « du »), une question hors sujet trouvait
    toujours la moitié de ses mots dans une slide et n'était jamais refusée.
    """

    def scorer(self, requete: str, textes: list[str]) -> list[float]:
        from agents.resources import mots_cles

        cles = mots_cles(requete)
        if not cles:
            return [0.0 for _ in textes]
        return [len(cles & mots_cles(t)) / len(cles) for t in textes]


class Tuteur:
    """Le tuteur multi-agent de bout en bout (O5).

    Les cours ingérés ou ajoutés sont visibles par tous les agents (``brancher_cours``) et
    indexés pour le Q&A. Les appels sont sérialisés : un seul LLM local répond à la fois.
    """

    def __init__(
        self,
        modeles: Modeles | None = None,
        *,
        recherche: Any | None = None,
        critic: bool = True,
        dossier_sortie: Path | None = None,
    ) -> None:
        self.modeles: Modeles = modeles or modeles_par_defaut()
        self.recherche = recherche or construire_recherche(self.modeles)
        self.dossier_sortie = dossier_sortie
        self.cours: dict[str, Course] = {}
        qz.brancher_cours(self.cours.get)
        # Le reranker léger note la part des mots de la question présents dans la slide : sous la
        # moitié, la question n'est pas dans le cours (bge-reranker, lui, garde le seuil de B3).
        self.agent_qa = AgentQA(self.recherche, seuil=SEUIL_QA_LEGER) if self.modeles == "leger" else AgentQA(self.recherche)
        agents: dict[Intention, Callable[[TutorState], dict[str, Any]]] = {
            "expliquer": explainer_agent,
            "question": self.agent_qa,
            "quiz": quiz_verifie_agent,
            "ressources": resources_agent,
        }
        self.graphe = construire_graphe(agents, critic=critic_agent if critic else None)
        self._verrou = threading.Lock()
        log.info("tuteur prêt (modèles %s, Critic %s)", self.modeles, "actif" if critic else "coupé")

    # ------------------------------------------------------------------ cours

    def ajouter_cours(self, cours: Course) -> int:
        """Rendre un cours disponible aux agents et l'indexer pour le Q&A. Renvoie le nombre de chunks."""
        from rag.index import indexer_cours

        self.cours[cours.id] = cours
        store = self.recherche.recherche.store
        n = indexer_cours(store, cours)
        self.recherche.recherche.rafraichir()  # reconstruire BM25 avec le nouveau cours
        return n

    def charger_dossier(self, dossier: Path | None = None) -> list[str]:
        """Ajouter tous les ``<dossier>/*/course.json`` déjà ingérés (par défaut ``data/processed``)."""
        from rag.index import charger_cours, fichiers_cours

        ids = []
        for fichier in fichiers_cours(dossier or self.dossier_sortie or DOSSIER_PROCESSED):
            cours = charger_cours(fichier)
            self.ajouter_cours(cours)
            ids.append(cours.id)
        return ids

    def ingerer(self, fichier: Path | str, *, rapide: bool | None = None, course_id: str | None = None) -> Course:
        """Ingestion de Ghayth (H1 → H2 → H3), puis indexation : le cours est prêt pour les agents.

        ``rapide`` (H1 texte seul, sans rendu ni OCR ni VLM) vaut par défaut ``INGESTION_RAPIDE``
        (``.env``), sinon ``True`` en modèles légers et ``False`` en modèles complets.
        """
        from ingestion import ingest

        if rapide is None:
            env = os.getenv("INGESTION_RAPIDE", "").strip().lower()
            rapide = env in ("1", "true", "oui") if env else self.modeles == "leger"
        cours = ingest(fichier, course_id, vlm=not rapide, llm=None if self.modeles == "complet" else False,
                       texte_brut=rapide, dossier_sortie=self.dossier_sortie)
        self.ajouter_cours(cours)
        return cours

    # ------------------------------------------------------------------ agents

    def tour(self, etat: TutorState) -> TutorState:
        """Un tour complet du graphe (router → agent → Critic)."""
        with self._verrou:
            return executer(etat, self.graphe)

    def _repondre(self, etat: TutorState) -> AgentResponse:
        final = self.tour(etat)
        agent = NOEUD_AGENT.get(final.intention or "question", "qa")
        return AgentResponse(agent=agent, reponse=final.reponse, sources=final.sources,
                             score_fidelite=final.score_fidelite)

    def expliquer(self, course_id: str, numero: int, niveau: Niveau = "intermediaire",
                  langue: Langue = "fr") -> AgentResponse:
        """Explication de la slide (O2), vérifiée par le Critic (O3)."""
        return self._repondre(TutorState(course_id=course_id, slide_courante=numero, niveau=niveau,
                                         langue_reponse=langue, intention="expliquer"))

    def demander(self, course_id: str, numero: int, question: str, niveau: Niveau = "intermediaire",
                 langue: Langue = "fr", intention: Intention | None = None) -> AgentResponse:
        """Question libre : le router choisit l'agent (Q&A par défaut), puis le Critic vérifie."""
        return self._repondre(TutorState(course_id=course_id, slide_courante=numero, niveau=niveau,
                                         langue_reponse=langue, question=question, intention=intention))


_TUTEUR: Tuteur | None = None
_VERROU_CREATION = threading.Lock()


def tuteur_partage() -> Tuteur:
    """Le tuteur unique de l'application (créé au premier appel, cours déjà ingérés rechargés)."""
    global _TUTEUR
    with _VERROU_CREATION:
        if _TUTEUR is None:
            _TUTEUR = Tuteur()
            try:
                _TUTEUR.charger_dossier()
            except Exception as e:  # noqa: BLE001 - un course.json invalide ne doit pas bloquer l'API
                log.warning("cours déjà ingérés non rechargés : %s", e)
        return _TUTEUR


__all__ = ["Tuteur", "construire_recherche", "modeles_par_defaut", "tuteur_partage"]
