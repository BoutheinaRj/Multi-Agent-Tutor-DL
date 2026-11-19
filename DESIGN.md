---
name: Multi-Agent Tutor
description: Tuteur multi-agent pour supports de cours, dans le monde du logo (mascotte robot, bleu roi, marine, or).
colors:
  bleu: "#2350d8"
  bleu-fonce: "#1a3fb3"
  bleu-clair: "#4a86f5"
  bleu-ciel: "#eaf1ff"
  bleu-ciel-2: "#d9e6ff"
  or: "#f5b21f"
  or-doux: "#fff3d4"
  or-texte: "#7a5300"
  marine: "#0e1a3d"
  marine-2: "#33405f"
  gris: "#5d6782"
  filet: "#dfe6f5"
  filet-fort: "#c4d0ea"
  fond: "#f5f8ff"
  surface: "#ffffff"
  vert: "#187547"
  vert-doux: "#e3f5ec"
  rouge: "#c8433a"
  rouge-doux: "#fdeceb"
typography:
  display:
    fontFamily: "Nunito, Noto Sans Arabic, sans-serif"
    fontSize: "50px"
    fontWeight: 800
    lineHeight: 1
  headline:
    fontFamily: "Nunito, Noto Sans Arabic, sans-serif"
    fontSize: "27px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Nunito, Noto Sans Arabic, sans-serif"
    fontSize: "21px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  lead:
    fontFamily: "Nunito, Noto Sans Arabic, sans-serif"
    fontSize: "22px"
    fontWeight: 800
    lineHeight: 1.35
  body:
    fontFamily: "Atkinson Hyperlegible, Noto Sans Arabic, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "tnum"
  label:
    fontFamily: "Nunito, Noto Sans Arabic, sans-serif"
    fontSize: "15px"
    fontWeight: 800
    lineHeight: 1
  meta:
    fontFamily: "Atkinson Hyperlegible, Noto Sans Arabic, sans-serif"
    fontSize: "14.5px"
    fontWeight: 400
    lineHeight: 1.6
  math:
    fontFamily: "STIX Two Text, Noto Sans Math, serif"
    fontSize: "23px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  pill: "999px"
  lg: "18px"
  md: "16px"
  sm: "12px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.bleu}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.bleu-fonce}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.marine}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 18px"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.bleu-ciel}"
  button-ghost:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.bleu}"
    rounded: "{rounded.pill}"
    padding: "0 18px"
    height: "44px"
  source-chip:
    backgroundColor: "{colors.bleu-ciel}"
    textColor: "{colors.bleu}"
    rounded: "{rounded.pill}"
    padding: "0 10px"
  source-chip-hover:
    backgroundColor: "{colors.bleu}"
    textColor: "{colors.surface}"
  agent-disc:
    backgroundColor: "{colors.bleu}"
    textColor: "{colors.surface}"
    rounded: "{rounded.pill}"
    size: "32px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.marine}"
    rounded: "{rounded.lg}"
    padding: "22px 24px"
  callout-retenir:
    backgroundColor: "{colors.or-doux}"
    textColor: "{colors.marine}"
    rounded: "{rounded.sm}"
    padding: "14px 16px"
  choice:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.marine}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
    height: "56px"
  choice-correct:
    backgroundColor: "{colors.vert-doux}"
  choice-wrong:
    backgroundColor: "{colors.rouge-doux}"
  segmented:
    backgroundColor: "{colors.bleu-ciel}"
    textColor: "{colors.marine-2}"
    rounded: "{rounded.pill}"
    padding: "4px"
  input-question:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.marine}"
    rounded: "{rounded.pill}"
    padding: "5px 5px 5px 18px"
---

# Design System: Multi-Agent Tutor

> Système relevé sur les maquettes livrées (`docs/maquettes/cours.html`, `quiz.html`, `maquettes.css`, `maquettes.js`).
> Ces maquettes HTML/CSS/JS statiques sont la **référence visuelle du frontend React (Vite)** (tâche A5) : les jetons de
> `:root` deviennent les variables CSS (ou le thème) des composants React, et la mascotte SVG de `maquettes.js` devient
> un composant à états. Les valeurs s'aligneront sur la charte D1 (`docs/charte.md`) quand elle sera livrée.

## Overview

**Creative North Star: "Le tuteur a un visage"**

Le système sort entièrement du logo officiel (`docs/maquettes/img/logo.jpg`, contrainte binding de PRODUCT.md) : une
mascotte robot souriante à toque de diplômé, contours bleu marine épais et arrondis, disques bleu roi qui portent des
pictogrammes blancs, traits d'« éclat », un seul point d'or. L'interface reprend ces matériaux tels quels plutôt que de
les décorer : la mascotte est le visage du tuteur et change d'état quand un agent travaille ou quand l'étudiant répond ;
les disques deviennent les avatars des agents ; l'éclat devient le retour positif ; l'or marque la seule chose à
retenir.

La densité est celle d'un outil d'étude, pas d'une page vitrine : fond blanc à peine bleuté, panneaux blancs posés
dessus, tout en pilules et coins larges, titres en sans-serif arrondi très gras, lecture dans une police conçue pour la
lisibilité. Le ton visuel est encourageant et clair, crédible devant un jury d'enseignants. L'interface est trilingue
(FR / EN / AR) et passe entièrement en RTL en arabe.

Rejet confirmé : le tableau de bord SaaS anonyme à cartes grises. Le monde précédemment tiré (« tableau de l'amphi »,
sombre) a été remplacé par l'épinglage du logo et ne fait pas partie du système.

**Key Characteristics:**
- La mascotte du logo, redessinée en SVG, avec quatre états : sourit, réfléchit, contente, oups.
- Bleu roi pour l'action et les agents, marine pour le texte et les contours épais, or réservé à un seul accent.
- Contour marine épais (2.5px) sur ce qui « porte » le cours : cadre de la slide, flashcard, bouton secondaire.
- Pilules partout pour les contrôles ; panneaux à 18px de rayon.
- Chaque contenu généré porte sa source `[Slide N]` sous forme d'ovale bleu cliquable.
- Mouvement court et doux (ease-out), réduit mais pas supprimé sous `prefers-reduced-motion`.

## Colors

Une palette de logo : un bleu roi franc décliné en trois clartés, un marine presque noir pour l'encre, un or rare, et
deux couleurs de verdict (vert, rouge) qui n'apparaissent qu'après une réponse.

### Primary
- **Bleu roi** (bleu) : action principale (« Me tester », « Envoyer »), onglet actif, avatars d'agent, bulle de
  l'étudiant, trait tracé sous la formule clé, verso de la flashcard, score final.
- **Bleu roi profond** (bleu-fonce) : survol du bouton principal, titre de la slide affichée, niveau de Bloom.
- **Bleu clair** (bleu-clair) : yeux de la mascotte, point « vue » de la bande des slides, survol des choix et
  vignettes, disque de l'agent Q&A.
- **Bleu ciel** (bleu-ciel) et **bleu ciel appuyé** (bleu-ciel-2) : zones douces : rail des sélecteurs à curseur,
  ovale de source, bulle du tuteur, fond de formule sur la slide, halo de focus du champ de question, étapes à venir.

### Secondary
- **Or du gland** (or) : l'unique accent. Bordure de l'encadré « À retenir », étape courante du quiz, éclair de
  repérage autour de la slide quand une source y mène, gland de la toque.
- **Or pâle** (or-doux) : fond de l'encadré « À retenir » et de la vignette de la slide courante.
- **Or encre** (or-texte) : titre de l'encadré « À retenir » (l'or pur n'est pas lisible en texte).

### Tertiary
- **Vert validé** (vert) / **vert pâle** (vert-doux) : bonne réponse, point « testée », badge « Vérifié par le Critic ».
- **Rouge oups** (rouge) / **rouge pâle** (rouge-doux) : mauvaise réponse uniquement.

### Neutral
- **Marine encre** (marine) : texte, contours épais, langue active, contour de la mascotte.
- **Marine adouci** (marine-2) : texte secondaire des paragraphes, libellés inactifs.
- **Gris ardoise** (gris) : métadonnées, compteurs, placeholders, légende.
- **Filet** (filet) et **filet appuyé** (filet-fort) : séparateurs, bordures de panneau, bordures des choix ; bordure
  du champ au repos, bordure pointillée du refus honnête.
- **Fond bleuté** (fond) : fond de page. **Surface** (surface) : panneaux, boutons secondaires, cadre de slide.

### Named Rules
**The One Gold Rule.** L'or marque une seule chose par écran : ce qu'il faut retenir, ou là où l'on est. Jamais un
bouton, jamais une décoration.

**The Verdict Colors Rule.** Le vert et le rouge n'apparaissent qu'en réponse à un acte de l'étudiant (réponse au
quiz, vérification par le Critic). Ils ne colorent jamais l'interface au repos.

**The Logo Palette Rule.** Aucune teinte hors du logo et des deux couleurs de verdict. Toute nouvelle couleur passe
par la charte D1.

## Typography

**Display Font:** Nunito 700–800 (avec Noto Sans Arabic, sans-serif)
**Body Font:** Atkinson Hyperlegible 400/700 (avec Noto Sans Arabic, sans-serif)
**Label/Mono Font:** STIX Two Text pour les formules (avec Noto Sans Math, serif)

**Character:** Le sans-serif arrondi et très gras du lettrage du logo pour tout ce qui parle (titres, boutons, idée
clé) ; une police de lecture pensée pour la lisibilité pour tout ce qui explique. Les formules ont leur propre voix,
une vraie serif mathématique. Toutes les polices sont auto-hébergées (`docs/maquettes/fonts/`). En arabe, titres et
texte basculent sur Noto Sans Arabic.

### Hierarchy
- **Display** (800, 50px, 1) : le score final du quiz, seul.
- **Headline** (800, 27px cours / 30px quiz, 1.2, -0.01em, `text-wrap: balance`) : titre de page. 22–24px sous 980px.
- **Title** (800, 21px panneau ; 24px question de quiz, 1.35) : tête de panneau, énoncé de question.
- **Lead** (800, 22px, 1.35) : l'idée clé de l'explication, une phrase.
- **Body** (400, 16px, 1.6, chiffres tabulaires) : explications, bulles, choix (16.5px). Paragraphes à 68ch maximum.
- **Label** (800, 13–15px) : boutons, onglets, sélecteurs, sources, noms d'agent, titres de bloc (13.5px, bleu).
- **Meta** (400, 13.5–14.5px, gris) : position dans le cours, sous-titres, légende, compteurs.
- **Math** (STIX Two Text 400, 23px formule clé ; 28px verso de flashcard ; 17–21px sur la slide).

### Named Rules
**The Two Voices Rule.** Nunito parle (titres, contrôles, idée clé), Atkinson explique (tout texte courant). On ne
compose jamais un paragraphe en Nunito ni un bouton en Atkinson.

**The Real Math Rule.** Une formule est toujours en STIX Two Text (KaTeX en React), jamais en police d'interface.

## Layout

- **Page Cours** : grille deux colonnes `11fr / 9fr` (environ 55 / 45), largeur max 1440px, marges et gouttière de
  28px. À gauche, la colonne de la slide est collante (`top: 92px`) : titre, slide encadrée en 16:9, navigation, bande
  des slides, légende. À droite : panneau Explication puis panneau Questions.
- **Page Quiz** : une colonne de 860px max, `34px 24px 52px` de marge, pile espacée de 20px.
- **Barre du haut** collante, blanche translucide (90 %, flou 10px), filet en bas : marque, cours actuel, onglets
  Cours/Quiz poussés à droite, sélecteur FR/EN/AR.
- **Rythme** : pas de 4px ; espacements usuels 8, 12, 16, 20, 24, 28. Panneaux à 22–24px de marge interne
  (18px sur mobile), 30px pour la carte de question.
- **Sous 980px** : une colonne ; l'ordre devient titre, slide, navigation, bande, légende, explication, questions ; la
  slide perd son ratio fixe ; une barre d'actions fixe en bas (« Me tester », « Demander ») garde l'action principale
  à portée de pouce, avec `safe-area-inset-bottom`.
- **Sous 640px** : la barre du haut passe sur deux lignes (onglets en pleine largeur) ; « Envoyer » et les flèches de
  navigation deviennent des boutons icône de 44px avec libellé masqué accessible.
- **RTL** : propriétés logiques partout (`inline-start`, `block-end`) ; les icônes directionnelles portent la classe
  miroir et se retournent en arabe.

## Elevation & Depth

Système hybride et léger : des panneaux blancs posés sur un fond bleuté, séparés par un filet de 1px et une ombre
diffuse teintée de bleu. La profondeur vient d'abord du contraste blanc / fond et des contours marine, ensuite des
ombres. Les éléments actifs (bouton principal, onglet courant) portent une ombre colorée bleue qui les fait « lever ».

### Shadow Vocabulary
- **Ombre de panneau** (`box-shadow: 0 1px 2px rgba(14,26,61,.05), 0 12px 32px rgba(35,80,216,.08)`) : panneaux,
  cadre de slide.
- **Ombre forte** (`box-shadow: 0 18px 44px rgba(35,80,216,.18)`) : la flashcard, seul objet qu'on manipule.
- **Lueur d'action** (`box-shadow: 0 6px 16px rgba(35,80,216,.28)`) : bouton principal ; `0 4px 12px` à .3 pour
  l'onglet actif.
- **Curseur de sélecteur** (`box-shadow: 0 2px 8px rgba(14,26,61,.12)`) : la pastille blanche qui glisse dans les
  sélecteurs de niveau et de mode.

### Named Rules
**The Blue Shadow Rule.** Les ombres sont teintées du bleu du logo, diffuses et basses. Pas d'ombre grise neutre,
pas d'ombre décalée dure.

## Shapes

Formes du logo : rondes et pleines. Les contrôles sont des pilules (999px), les avatars et pastilles des disques
parfaits. Les conteneurs ont des coins larges : 18px pour les panneaux, la slide encadrée et la flashcard ; 16px pour
les choix de quiz et le retour ; 12px pour l'encadré « À retenir » ; 14px pour les vignettes. Les bulles de dialogue
ont 18px avec un coin réduit à 6px du côté de celui qui parle. Le contour épais marine (2.5px, l'épaisseur des traits
du logo) est réservé aux objets qui portent le cours ; les bordures de contrôle ordinaires font 2px en filet.

## Components

### Buttons
Pleins, arrondis et francs, comme le lettrage du logo.
- **Shape:** pilule (999px), 44px de haut minimum, 18px de marge horizontale, icône 20px et libellé Nunito 800 15px.
- **Primary:** bleu roi, texte blanc, lueur d'action bleue. Un seul par zone.
- **Secondary:** surface blanche, contour marine épais (2.5px), texte marine.
- **Ghost (discret):** sans contour, texte bleu roi.
- **Hover / Focus:** survol (seulement sur pointeur fin) vers bleu ciel, ou bleu profond pour le principal ; appui en
  `scale(.97)` sur 160ms ease-out. Désactivé : contour filet appuyé, texte gris.

### Chips
- **Source `[Slide N]`:** ovale bleu ciel, texte bleu roi Nunito 800 à 0.85em, dans le fil du texte ; au survol il
  passe en bleu plein, texte blanc ; un clic amène la slide et la fait clignoter d'un halo or (900ms).
- **Suggestions de questions:** pilules blanches à contour filet 2px, texte marine adouci ; survol bleu clair.

### Cards / Containers
- **Corner Style:** 18px.
- **Background:** surface blanche sur fond bleuté.
- **Shadow Strategy:** ombre de panneau (voir Elevation & Depth).
- **Border:** filet 1px.
- **Internal Padding:** 22–24px ; 18px sous 980px.
- **Cadre de slide:** contour marine épais 2.5px, 10px de marge, slide intérieure à 10px de rayon.
- **Encadré « À retenir »:** or pâle, bordure or 2px, disque or à pictogramme marine, titre en or encre.

### Inputs / Fields
- **Style:** champ de question en pilule, contour filet appuyé 2.5px, bouton « Envoyer » principal logé dedans.
- **Focus:** le contour passe au bleu roi avec un halo bleu ciel appuyé de 4px (`:focus-within`).

### Navigation
- **Onglets Cours / Quiz:** rail bleu ciel en pilule, 4px de marge ; onglet actif plein bleu roi, texte blanc, lueur
  bleue ; inactifs marine adouci, survol blanc et bleu.
- **Langues:** groupe de pilules à contour filet 1px ; langue active pleine marine, texte blanc.
- **Sélecteurs à curseur (niveau, mode QCM / flashcards):** rail bleu ciel, pastille blanche qui glisse en 220ms
  ease-out sous l'option choisie (texte bleu roi). Le sens s'inverse en RTL.
- **Bande des slides:** vignettes de 50×56px, bordure filet 2px, numéro et point de maîtrise dont la **taille et la
  couleur disent l'état** (5px filet, 7px bleu clair « vue », 9px bleu « comprise », 11px vert « testée ») ; slide
  courante en bordure marine sur or pâle ; fondu aux deux bords.

### Mascotte (composant signature)
Le visage du tuteur, redessiné du logo en SVG 100×100 (tête blanche à contour marine 3px, visière marine, yeux en arc
bleu clair, toque bleu roi, gland or). 40px dans la marque, 56–58px en tête de panneau, 76px en tête de quiz, 110px
sur le score. Quatre états via `data-etat` :
- **sourit** (repos) : yeux en arc.
- **réfléchit** (un agent génère) : les yeux deviennent trois points qui pulsent (900ms, décalés de 150ms) ; le
  contenu en cours de génération passe à 25 % d'opacité avec un flou de 2px.
- **contente** (bonne réponse) : la tête se redresse (`translateY(-2px) rotate(-4deg)`) et les trois traits d'éclat
  du logo apparaissent en 360ms, échelonnés.
- **oups** (erreur, refus) : yeux en traits, tête penchée de 5°, retour au repos après 1.6s.

### Avatars d'agent
Disque de 32px plein (bleu roi par défaut ; bleu clair, marine ou vert selon l'agent) portant un pictogramme blanc de
17px, suivi du nom de l'agent en Nunito 800 14px. Chaque agent garde sa couleur.

### Fil de questions
Bulle étudiant bleu roi à droite, bulle tuteur bleu ciel à gauche précédée de la mascotte ; le refus honnête
(« ce n'est pas dans le cours ») est une bulle blanche à bordure pointillée filet appuyé 2px. Les tours entrent en
260ms (fondu et 8px de montée) ; la réponse s'écrit avec un curseur bleu qui pulse.

### Quiz et flashcards
- **Choix:** ligne de 56px min, rayon 16px, bordure filet 2px, lettre dans un disque bleu ciel ; bonne réponse en
  vert pâle (bordure et disque verts), mauvaise en rouge pâle ; les autres options passent à 50 %.
- **Progression:** barres de 8px en pilule, étape courante or, juste vert, fausse rouge.
- **Flashcard:** 300px de haut, contour marine épais, ombre forte ; retournement 3D de 420ms ease-in-out vers un
  verso bleu roi plein dont la réponse est en STIX Two Text 28px. Sous mouvement réduit, le retournement devient un
  simple échange de faces.

### Motion
Courbes : `cubic-bezier(.23,1,.32,1)` pour les entrées et retours d'état, `cubic-bezier(.77,0,.175,1)` pour les
transformations symétriques (flashcard, pulsations). Durées de 160ms (états de contrôle) à 450ms (trait tracé sous la
formule clé). Sous `prefers-reduced-motion`, les transformations et entrées disparaissent mais les fondus de couleur
et d'opacité restent.

## Do's and Don'ts

### Do:
- **Do** mettre la mascotte en état « réfléchit » pendant chaque génération d'agent (SSE de l'Explainer et du Q&A) et
  la ramener au repos à la fin.
- **Do** rendre chaque `[Slide N]` comme un ovale de source cliquable qui mène à la slide.
- **Do** réserver le contour marine épais (2.5px) aux objets qui portent le cours : slide, flashcard, bouton
  secondaire.
- **Do** utiliser des propriétés logiques (`inline-start`, `block-end`) et retourner les icônes directionnelles pour
  que l'arabe passe en RTL sans CSS supplémentaire.
- **Do** garder les cibles tactiles à 44px minimum et l'action principale dans la barre fixe du bas sous 980px.
- **Do** composer les formules en STIX Two Text (KaTeX dans le frontend React).

### Don't:
- **Don't** sortir de la palette du logo : pas de nouvelle teinte, pas de thème sombre, pas de dégradé décoratif.
- **Don't** utiliser l'or pour un bouton ou une décoration : il marque une seule chose par écran.
- **Don't** construire des écrans en tableau de bord SaaS à cartes grises anonymes ; le tuteur a la mascotte pour visage.
- **Don't** mettre de vert ou de rouge sur l'interface au repos : ce sont des verdicts.
