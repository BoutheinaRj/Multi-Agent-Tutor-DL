"""O5 — Démo de bout en bout du tuteur sur 2 vrais cours du corpus.

Pour chaque cours : dépôt (ingestion H1 → H2 → H3 + indexation B1-B2), explication d'une slide
(O2 + Critic O3), une question du cours (B3 + Critic), une question hors cours (refus attendu),
un quiz (A2 vérifié par le Critic) et des ressources (A4). Affiche les temps, les sources et les
scores du Critic ; ``--rapport`` écrit le même compte rendu en Markdown (utile pour P1).

Usage :

    python -m tools.demo_o5                       # modèles de .env (TUTEUR_MODELES, LLM_BACKEND)
    python -m tools.demo_o5 --leger --rapide      # sans aucun modèle : vérifie le câblage en 10 s
    python -m tools.demo_o5 --rapport docs/demo_o5.md

Tout tourne en local : aucune API externe.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from agents.tuteur import Tuteur
from schemas import AgentResponse

RACINE = Path(__file__).resolve().parent.parent


@dataclass
class Scenario:
    fichier: str
    slide: int
    question: str
    hors_cours: str
    langue: str = "fr"


SCENARIOS = [
    Scenario("data/corpus/fr/ml/ml_gradient_stochastique_esprit_fr.pdf", 7,
             "Pourquoi le pas doit-il décroître ?", "Qui a gagné la coupe du monde 2018 ?"),
    Scenario("data/corpus/en/dl/dl_cnn_ntu_en.pptx", 7,
             "Why does a neuron not need to see the whole image?", "Who won the 2018 World Cup?", "en"),
]


@dataclass
class Ligne:
    etape: str
    duree: float
    resultat: str
    details: list[str] = field(default_factory=list)


def _resume(rep: AgentResponse, n: int = 160) -> str:
    texte = " ".join(rep.reponse.split())
    return texte[:n] + ("…" if len(texte) > n else "")


def _info(rep: AgentResponse) -> str:
    sources = ", ".join(str(s.numero) for s in rep.sources) or "aucune"
    score = "—" if rep.score_fidelite is None else f"{rep.score_fidelite:.2f}"
    return f"agent {rep.agent} · slides {sources} · Critic {score}"


def chrono(f, *args, **kwargs):  # type: ignore[no-untyped-def]
    debut = time.perf_counter()
    resultat = f(*args, **kwargs)
    return resultat, time.perf_counter() - debut


def jouer(tuteur: Tuteur, sc: Scenario, rapide: bool | None) -> tuple[str, list[Ligne]]:
    lignes: list[Ligne] = []
    cours, d = chrono(tuteur.ingerer, RACINE / sc.fichier, rapide=rapide)
    figures = sum(len(s.description_figures) for s in cours.slides)
    concepts = len({c for s in cours.slides for c in s.concepts})
    lignes.append(Ligne("Dépôt et ingestion", d, f"{cours.nombre_slides} slides, {figures} figures décrites, "
                        f"{concepts} notions, langue {cours.langue}"))
    titre = cours.slides[sc.slide - 1].titre or f"slide {sc.slide}"

    rep, d = chrono(tuteur.expliquer, cours.id, sc.slide, "debutant", sc.langue)
    lignes.append(Ligne(f"Explication slide {sc.slide} « {titre} » (débutant)", d, _info(rep), [_resume(rep)]))

    rep, d = chrono(tuteur.demander, cours.id, sc.slide, sc.question, "intermediaire", sc.langue)
    lignes.append(Ligne(f"Question : {sc.question}", d, _info(rep), [_resume(rep)]))

    rep, d = chrono(tuteur.demander, cours.id, sc.slide, sc.hors_cours, "intermediaire", sc.langue)
    refus = "pas dans le cours" in rep.reponse
    lignes.append(Ligne(f"Hors cours : {sc.hors_cours}", d, ("refus ✓" if refus else "PAS DE REFUS ✗") + f" · {_info(rep)}"))

    rep, d = chrono(tuteur.demander, cours.id, sc.slide, "Fais-moi un quiz sur cette slide", "intermediaire",
                    sc.langue, intention="quiz")
    lignes.append(Ligne("Quiz vérifié par le Critic", d, _info(rep), [_resume(rep, 200)]))

    rep, d = chrono(tuteur.demander, cours.id, sc.slide, "Des ressources pour aller plus loin", "intermediaire",
                    sc.langue, intention="ressources")
    lignes.append(Ligne("Ressources (catalogue local)", d, _info(rep), [_resume(rep)]))
    return cours.id, lignes


def rapport(tuteur: Tuteur, resultats: list[tuple[str, list[Ligne]]], total: float) -> str:
    import os

    out = ["# Démo O5 — tuteur de bout en bout", "",
           f"Modèles : `{tuteur.modeles}` · LLM : `{os.getenv('LLM_BACKEND', 'llamacpp')}` · "
           f"durée totale {total:.1f} s · aucune API externe.", ""]
    for course_id, lignes in resultats:
        out += [f"## {course_id}", "", "| Étape | Durée | Résultat |", "|---|---|---|"]
        for l in lignes:
            out.append(f"| {l.etape} | {l.duree:.1f} s | {l.resultat} |")
        out.append("")
        for l in lignes:
            for det in l.details:
                out.append(f"- **{l.etape}** : {det}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Démo O5 de bout en bout sur 2 cours")
    parser.add_argument("--leger", action="store_true", help="modèles légers (aucun téléchargement)")
    parser.add_argument("--rapide", action="store_true", help="ingestion texte seul (sans rendu, OCR ni VLM)")
    parser.add_argument("--rapport", type=Path, help="écrire le compte rendu Markdown dans ce fichier")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    debut = time.perf_counter()
    tuteur = Tuteur("leger" if args.leger else None)
    resultats = [jouer(tuteur, sc, True if args.rapide else None) for sc in SCENARIOS]
    texte = rapport(tuteur, resultats, time.perf_counter() - debut)
    print(texte)
    if args.rapport:
        args.rapport.write_text(texte + "\n", encoding="utf-8")
        print(f"\nCompte rendu écrit dans {args.rapport}")
    refus_manques = sum("PAS DE REFUS" in l.resultat for _, lignes in resultats for l in lignes)
    return 1 if refus_manques else 0


if __name__ == "__main__":
    raise SystemExit(main())
