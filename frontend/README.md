# frontend/

Responsable : Ali — tâche A5 (voir la répartition des tâches).

Interface React + Vite + TypeScript du tuteur, d'après les maquettes D2 d'Ons (`docs/maquettes/`, branche `ons`,
et `DESIGN.md`) et la charte D1 de Both (`docs/charte.md`, branche `both`).

**Tout est servi en local** : aucune API externe, aucun CDN, aucune Google Fonts. Les polices (Inter, Noto Sans
Arabic, STIX Two Text, Noto Sans Math) sont dans `public/fonts/`, le logo et le favicon dans `public/img/`, et KaTeX
(formules LaTeX) est installé par npm avec ses polices. Le seul serveur appelé est l'API du projet (`VITE_API_URL`).
Les liens des ressources (Wikipédia, YouTube…) ne s'ouvrent que si l'étudiant clique dessus.

## Lancer

Il faut Node.js 20 ou plus récent, et l'API lancée à côté.

```bash
# 1. L'API, depuis la racine du dépôt (port 8000)
.venv\Scripts\activate          # Windows ; source .venv/bin/activate sous Linux/macOS
uvicorn api.main:app --reload

# 2. Le frontend, dans un second terminal (port 5173)
cd frontend
cp .env.example .env            # puis ajuster VITE_API_URL si l'API n'est pas sur localhost:8000
npm install
npm run dev                     # http://localhost:5173
```

Autres commandes : `npm run build` (vérification TypeScript + build dans `dist/`), `npm run preview` (sert `dist/`
sur le port 5173), `npm run typecheck`.

Le port 5173 est fixé (`strictPort`) car c'est l'origine autorisée par CORS dans `api/main.py`. Si une autre
application l'occupe déjà, Vite s'arrête au lieu de prendre un autre port : libère le port ou ajoute l'origine dans
`ORIGINES_FRONTEND`.

## Configuration (`frontend/.env`)

| Variable | Défaut | Rôle |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL de l'API FastAPI |
| `VITE_COURS_PAR_DEFAUT` | `ml_regression_lineaire_fr` | Cours ouvert au premier lancement (le cours d'exemple de l'API) |

`.env` est ignoré par Git (règle racine) : `.env.example` est le modèle versionné.

## Pages et routes utilisées

| Page | Zone | Route |
|---|---|---|
| Barre du haut | import d'un support PDF/PPTX | `POST /upload` |
| Cours | slide à gauche (titre, texte, formules KaTeX, figures), navigation, bande de maîtrise | `GET /course/{id}` |
| Cours | explication à 3 niveaux (débutant / intermédiaire / avancé) | `GET /slide/{id}/explain?niveau=` |
| Cours | ressources de la slide (titre, type, justification, lien) | `GET /resources?slide_id=&niveau=&langue=` |
| Cours | chat Q&A avec citations `[Slide N]` | `POST /ask` |
| Quiz | QCM une question à la fois, retour immédiat, score | `GET /quiz?course_id=&slide=&n=&langue=` |
| Quiz | flashcards : cartes dues, sinon génération puis enregistrement | `GET /flashcards/due`, `GET /flashcards`, `POST /flashcards/save` |
| Quiz | notation SM-2 de 0 à 5 | `POST /flashcards/{id}/review` |
| Quiz | export Anki (.apkg) | `GET /flashcards/export` |

- **Langue** : FR / EN / AR dans la barre du haut ; en arabe, la page passe en RTL (`dir="rtl"`). La langue est
  envoyée à `/ask`, `/quiz`, `/flashcards` et `/resources`.
- **Citations** : `[Slide N]`, `[Slides 3, 5]` et `[Slide 3-5]` deviennent des pastilles jaunes cliquables qui
  amènent à la slide (depuis le quiz aussi). Les sources renvoyées mais non citées dans le texte sont ajoutées en fin
  de réponse. Une réponse du Q&A sans aucune source est affichée comme un refus honnête (bulle en pointillés).
- **Formules** : `$…$`, `$$…$$`, `\(…\)`, `\[…\]` dans les réponses, et `Slide.formules_latex` sur la slide.
- **Utilisateur SRS** : identifiant gardé dans `localStorage` (`mat-user`, `etudiant` par défaut).
- **Maîtrise** (bande des slides) : *vue* = slide affichée, *comprise* = explication reçue, *testée* = question de
  quiz répondue. Gardée dans `localStorage`, par cours.
- **Clavier** : ← / → changent de slide ; 1–4 ou A–D répondent au QCM ; Espace retourne la flashcard, 0–5 la note.

## LLM local lent et streaming (A3)

`/explain` et `/ask` sont encore factices (A3 viendra après O2). Le LLM local peut mettre 30 à 120 s : pendant la
génération, la mascotte « réfléchit », un compteur affiche le temps écoulé (avec un avertissement après 15 s) et un
bouton permet d'annuler. Les explications déjà reçues sont gardées en cache (slide × niveau) et un délai de 300 ms
évite de lancer une génération à chaque slide quand on navigue vite.

L'affichage est déjà progressif. `lireReponseAgent` (`src/api.ts`) accepte deux formats, sans changement côté
frontend le jour où A3 passe au streaming :

- **JSON** (`application/json`, actuel) : `AgentResponse`, dont le texte est révélé mot à mot ;
- **SSE** (`text/event-stream`, prévu) : chaque événement `data:` est soit `{"token": "…"}` (morceau de texte),
  soit l'`AgentResponse` final (`{"agent": …, "reponse": …, "sources": […]}`), soit du texte brut. Le frontend
  envoie `Accept: text/event-stream, application/json`.

## Arborescence

```
frontend/
├── public/fonts/        polices woff2 (copiées de docs/maquettes/fonts/, branche ons)
├── public/img/          logo, logo-icone, logo-tete, favicon (copiés de assets/, branche both)
└── src/
    ├── api.ts           client de l'API, lecture JSON/SSE, export Anki
    ├── types.ts         miroir TypeScript de schemas/models.py et api/models.py
    ├── i18n.tsx         libellés FR / EN / AR, bascule RTL
    ├── maitrise.ts      état vue / comprise / testée des slides
    ├── components/      barre du haut, mascotte, icônes, texte riche (KaTeX + citations), attente
    ├── pages/           Cours, Quiz, Flashcards
    └── styles/          maquettes.css (copie de la maquette D2) + app.css (états réels de l'API)
```

`types.ts` est maintenu à la main : toute évolution de `schemas/models.py` ou `api/models.py` doit y être reportée.

## Limites connues

- Le rendu PNG des slides (`Slide.image_rendu`) n'est pas encore servi par l'API : la slide est affichée à partir de
  son texte, de ses formules et de la description de ses figures.
- « Écouter » (lecture audio, A7) est affiché mais désactivé.
