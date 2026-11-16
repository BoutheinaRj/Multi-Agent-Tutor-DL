
"""
G1 — Analyse statistique des supports de cours PDF/PPTX.

Ce script permet de calculer :
- Le nombre total de slides/pages.
- Le nombre de mots et d'images par slide.
- La moyenne, le minimum et le maximum de mots.
- Les slides presque vides (moins de 10 mots).
- L'export des résultats au format JSON.
"""

import argparse
import json
import re
from pathlib import Path
from statistics import mean

import pymupdf
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


# Seuil défini dans le cahier des charges.
EMPTY_THRESHOLD = 10


def count_words(text):
    """Compter les mots dans un texte Unicode."""
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def extract_pdf(path):
    """Extraire les statistiques de chaque page PDF."""
    slides = []

    # Ouvrir le document PDF avec PyMuPDF.
    with pymupdf.open(str(path)) as document:
        for index, page in enumerate(document, start=1):

            # Extraire le texte de la page.
            text = page.get_text("text")

            # Compter les images affichées dans la page.
            images = len(page.get_image_info())

            slides.append({
                "slide": index,
                "words": count_words(text),
                "images": images,
            })

    return slides


def iter_shapes(shapes):
    """Parcourir les objets PPTX, y compris les groupes."""
    for shape in shapes:

        # Explorer également les formes groupées.
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from iter_shapes(shape.shapes)
        else:
            yield shape


def extract_pptx(path):
    """Extraire les statistiques de chaque slide PowerPoint."""
    presentation = Presentation(str(path))
    slides = []

    for index, slide in enumerate(presentation.slides, start=1):
        text_parts = []
        images = 0

        # Parcourir tous les objets de la slide.
        for shape in iter_shapes(slide.shapes):

            # Compter les images intégrées.
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                images += 1

            # Extraire le contenu des zones de texte.
            if shape.has_text_frame:
                text_parts.append(shape.text)

            # Extraire le texte contenu dans les tableaux.
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        text_parts.append(cell.text)

        text = " ".join(text_parts)

        slides.append({
            "slide": index,
            "words": count_words(text),
            "images": images,
        })

    return slides


def analyze_file(file_path):
    """Analyser un document et calculer les statistiques."""
    path = Path(file_path)

    # Vérifier que le fichier existe.
    if not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    extension = path.suffix.lower()

    # Sélectionner le lecteur selon le format.
    if extension == ".pdf":
        slides = extract_pdf(path)
    elif extension == ".pptx":
        slides = extract_pptx(path)
    else:
        raise ValueError("Format non supporté : utiliser PDF ou PPTX.")

    word_counts = [slide["words"] for slide in slides]

    # Identifier les slides contenant moins de 10 mots.
    almost_empty = [
        slide["slide"]
        for slide in slides
        if slide["words"] < EMPTY_THRESHOLD
    ]

    # Préparer un résultat structuré.
    return {
        "file": path.name,
        "format": extension.lstrip("."),
        "total_slides": len(slides),
        "mean_words": round(mean(word_counts), 2) if word_counts else 0,
        "min_words": min(word_counts, default=0),
        "max_words": max(word_counts, default=0),
        "almost_empty_slides": almost_empty,
        "slides": slides,
    }


def main():
    """Point d'entrée de l'interface en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Analyser les slides d'un cours PDF ou PPTX."
    )

    # Chemin du document à analyser.
    parser.add_argument(
        "file",
        help="Chemin du fichier PDF ou PPTX"
    )

    # --json : affichage JSON ou export dans un fichier.
    parser.add_argument(
        "--json",
        nargs="?",
        const="-",
        default=None,
        metavar="FICHIER",
        help="Exporter en JSON (stdout ou fichier)"
    )

    args = parser.parse_args()

    # Analyser le document et gérer les erreurs d'entrée.
    try:
        results = analyze_file(args.file)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    if args.json is not None:
        output = json.dumps(results, indent=2, ensure_ascii=False)

        if args.json == "-":
            print(output)
        else:
            output_path = Path(args.json)
            output_path.write_text(output, encoding="utf-8")
            print(f"JSON exporté : {output_path}")
    else:
        # Affichage lisible dans le terminal.
        print(f"\nDocument : {results['file']}")
        print(f"Format : {results['format']}")
        print(f"Nombre de slides : {results['total_slides']}")
        print(f"Moyenne des mots : {results['mean_words']}")
        print(f"Minimum : {results['min_words']}")
        print(f"Maximum : {results['max_words']}")
        print(f"Slides presque vides : {results['almost_empty_slides']}")

        for slide in results["slides"]:
            print(
                f"Slide {slide['slide']} : "
                f"{slide['words']} mots, "
                f"{slide['images']} images"
            )


if __name__ == "__main__":
    main()
