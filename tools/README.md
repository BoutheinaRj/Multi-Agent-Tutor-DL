
# G1 — Slide Statistics CLI

## Description

`slide_stats.py` est un outil Python en ligne de commande
permettant d'analyser des supports de cours PDF et PPTX.

Il calcule :
- Le nombre total de slides/pages
- Le nombre de mots par slide
- Le nombre d'images par slide
- La moyenne des mots par slide
- Le minimum et le maximum de mots
- Les slides presque vides (moins de 10 mots)

## Prérequis

- Python 3.11
- PyMuPDF
- python-pptx
- pytest (pour les tests)

## Installation

Depuis la racine du repository :

```powershell
# Installer les dépendances nécessaires
python -m pip install pymupdf python-pptx pytest
```

## Utilisation

### Analyser un PDF

```powershell
python tools/slide_stats.py cours.pdf
```

### Analyser un PowerPoint

```powershell
python tools/slide_stats.py cours.pptx
```

### Afficher les résultats en JSON

```powershell
python tools/slide_stats.py cours.pdf --json
```

### Exporter les résultats dans un fichier JSON

```powershell
python tools/slide_stats.py cours.pdf --json resultats.json
```

### Afficher l'aide

```powershell
python tools/slide_stats.py --help
```

## Structure du résultat JSON

```json
{
  "file": "cours.pdf",
  "format": "pdf",
  "total_slides": 2,
  "mean_words": 6.5,
  "min_words": 2,
  "max_words": 11,
  "almost_empty_slides": [2],
  "slides": [
    {"slide": 1, "words": 11, "images": 0},
    {"slide": 2, "words": 2, "images": 0}
  ]
}
```

## Tests automatisés

Depuis la racine du repository :

```powershell
# Exécuter les tests unitaires
python -m pytest tests/test_slide_stats.py -v
```

Les quatre tests couvrent :
1. Analyse PDF
2. Analyse PPTX
3. Gestion d'un format non supporté
4. Export JSON via CLI

Résultat validé : 4 tests réussis.

## Limites

- Les PDF scannés sans couche de texte nécessitent
  une étape OCR pour compter les mots.
- Le comptage des mots repose sur une expression régulière.
- Les images vectorielles ne sont pas toutes comptabilisées.
- Les slides presque vides contiennent moins de 10 mots
  extractibles, même si elles comportent des images.

## Intégration au projet

Le script est un outil indépendant destiné à fournir
des statistiques descriptives sur les supports de cours.

Il peut également servir à renseigner le nombre de slides
dans `data/corpus_extra/inventaire.csv` pour la tâche G2.

# O5 — Démo de bout en bout (`demo_o5.py`)

Joue le parcours complet sur 2 vrais cours du corpus (un PDF français, un PPTX anglais) : dépôt et
ingestion, explication d'une slide, question du cours, question hors cours (refus attendu), quiz
vérifié et ressources, avec les temps et les scores du Critic.

```bash
python -m tools.demo_o5 --leger --rapide        # sans aucun modèle, en ~10 s
python -m tools.demo_o5 --rapport docs/demo_o5.md   # modèles de .env, compte rendu Markdown
```
