
"""Tests automatisés du script G1 slide_stats.py."""

import json
import subprocess
import sys
from pathlib import Path

import pymupdf
import pytest
from PIL import Image
from pptx import Presentation

# Rendre le dossier tools accessible aux tests.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from slide_stats import analyze_file


@pytest.fixture
def sample_pdf(tmp_path):
    """Créer un PDF temporaire pour les tests."""
    path = tmp_path / "cours.pdf"
    doc = pymupdf.open()

    page1 = doc.new_page()
    page1.insert_text(
        (72, 72),
        "Un deux trois quatre cinq six sept huit neuf dix onze"
    )

    page2 = doc.new_page()
    page2.insert_text((72, 72), "Quiz rapide")

    doc.save(str(path))
    doc.close()

    return path


def test_pdf(sample_pdf):
    """Vérifier les statistiques d'un PDF de deux pages."""
    result = analyze_file(sample_pdf)

    assert result["total_slides"] == 2
    assert result["mean_words"] == 6.5
    assert result["min_words"] == 2
    assert result["max_words"] == 11
    assert result["almost_empty_slides"] == [2]
    assert result["slides"][0]["images"] == 0


def test_pptx(tmp_path):
    """Vérifier le texte et les images d'un PowerPoint."""
    path = tmp_path / "cours.pptx"
    image_path = tmp_path / "image.png"

    # Créer une image temporaire.
    Image.new("RGB", (50, 50), "white").save(image_path)

    presentation = Presentation()

    slide1 = presentation.slides.add_slide(
        presentation.slide_layouts[6]
    )
    slide1.shapes.add_textbox(
        914400, 914400, 7000000, 1000000
    ).text = "Un deux trois quatre cinq six sept huit neuf dix onze"
    slide1.shapes.add_picture(str(image_path), 914400, 2000000)

    slide2 = presentation.slides.add_slide(
        presentation.slide_layouts[6]
    )
    slide2.shapes.add_textbox(
        914400, 914400, 7000000, 1000000
    ).text = "Quiz rapide"

    presentation.save(str(path))

    result = analyze_file(path)

    assert result["total_slides"] == 2
    assert result["mean_words"] == 6.5
    assert result["slides"][0]["images"] == 1
    assert result["slides"][1]["images"] == 0
    assert result["almost_empty_slides"] == [2]


def test_format_invalide(tmp_path):
    """Vérifier le rejet des fichiers non supportés."""
    path = tmp_path / "cours.txt"
    path.write_text("Contenu de test", encoding="utf-8")

    with pytest.raises(ValueError, match="Format non supporté"):
        analyze_file(path)


def test_json_cli(sample_pdf):
    """Vérifier que la CLI produit un JSON valide."""
    script = ROOT / "tools" / "slide_stats.py"

    # Exécuter le script dans un processus Python séparé.
    process = subprocess.run(
        [sys.executable, str(script), str(sample_pdf), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )

    # Vérifier le contenu JSON retourné.
    result = json.loads(process.stdout)

    assert result["total_slides"] == 2
    assert result["mean_words"] == 6.5
    assert result["almost_empty_slides"] == [2]
