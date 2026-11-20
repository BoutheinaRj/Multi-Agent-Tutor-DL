// Application : barre du haut, page Cours ou Quiz, écran d'accueil s'il n'y a pas de cours.
import { useEffect, useState } from "react";
import { api, ErreurApi, utilisateur } from "./api";
import { Attente, Erreur } from "./components/Attente";
import { Barre, Televersement, type Page } from "./components/Barre";
import { SpriteIcones } from "./components/Icones";
import { useLangue } from "./i18n";
import { useMaitrise } from "./maitrise";
import { PageCours } from "./pages/Cours";
import { PageQuiz, type ModeQuiz } from "./pages/Quiz";
import type { Course, Niveau } from "./types";

const COURS_PAR_DEFAUT = import.meta.env.VITE_COURS_PAR_DEFAUT || "ml_regression_lineaire_fr";
const pageDuHash = (): Page => (location.hash === "#quiz" ? "quiz" : "cours");

export default function App() {
  const { t } = useLangue();
  const [cours, setCours] = useState<Course | null>(null);
  const [chargement, setChargement] = useState(true);
  const [page, setPage] = useState<Page>(pageDuHash);
  const [numero, setNumero] = useState(1);
  const [niveau, setNiveau] = useState<Niveau>(() => (localStorage.getItem("mat-niveau") as Niveau) || "intermediaire");
  const [portee, setPortee] = useState<number | null>(null);
  const [modeQuiz, setModeQuiz] = useState<ModeQuiz>("qcm");
  const [erreur, setErreur] = useState<string | null>(null);
  const { maitrise, marquer } = useMaitrise(cours?.id ?? null);
  const user = utilisateur();

  // Cours ouvert au démarrage : le dernier ouvert, sinon celui de VITE_COURS_PAR_DEFAUT.
  useEffect(() => {
    const id = localStorage.getItem("mat-cours") || COURS_PAR_DEFAUT;
    api
      .cours(id)
      .then(ouvrir)
      .catch((e) => {
        if (!(e instanceof ErreurApi && e.statut === 404)) setErreur(e instanceof ErreurApi ? e.message : String(e));
        localStorage.removeItem("mat-cours");
      })
      .finally(() => setChargement(false));
  }, []);

  useEffect(() => {
    const surHash = () => setPage(pageDuHash());
    addEventListener("hashchange", surHash);
    return () => removeEventListener("hashchange", surHash);
  }, []);

  function ouvrir(c: Course) {
    setCours(c);
    setErreur(null);
    localStorage.setItem("mat-cours", c.id);
    const n = Number(localStorage.getItem(`mat-slide-${c.id}`)) || 1;
    setNumero(Math.min(Math.max(1, n), c.nombre_slides));
    setPortee(null);
  }

  function allerPage(p: Page) {
    setPage(p);
    history.replaceState(null, "", `#${p}`);
    scrollTo({ top: 0 });
  }

  const changerNumero = (n: number) => {
    setNumero(n);
    if (cours) localStorage.setItem(`mat-slide-${cours.id}`, String(n));
  };
  const changerNiveau = (n: Niveau) => {
    setNiveau(n);
    localStorage.setItem("mat-niveau", n);
  };
  const allerSlide = (n: number) => {
    changerNumero(n);
    allerPage("cours");
  };

  return (
    <>
      <SpriteIcones />
      <Barre
        cours={cours}
        page={page}
        surPage={(p) => {
          if (p === "quiz") {
            setPortee(null);
            setModeQuiz("qcm");
          }
          allerPage(p);
        }}
        surCours={(c) => {
          ouvrir(c);
          allerPage("cours");
        }}
        surErreur={setErreur}
      />
      {erreur && (
        <div className="bandeau-erreur">
          <Erreur message={erreur} />
          <button type="button" className="bouton discret" onClick={() => setErreur(null)} aria-label={t("annuler")}>
            ×
          </button>
        </div>
      )}
      {chargement ? (
        <main className="accueil">
          <Attente />
        </main>
      ) : !cours ? (
        <main className="accueil">
          <img src="/img/logo.png" alt="Multi-Agent Tutor" width={320} />
          <h1>{t("accueil-titre")}</h1>
          <p>{t("accueil-texte")}</p>
          <Televersement surCours={ouvrir} surErreur={setErreur} />
        </main>
      ) : page === "cours" ? (
        <PageCours
          cours={cours}
          numero={numero}
          surNumero={changerNumero}
          niveau={niveau}
          surNiveau={changerNiveau}
          maitrise={maitrise}
          surMaitrise={marquer}
          surTester={(n) => {
            setPortee(n);
            setModeQuiz("qcm");
            allerPage("quiz");
          }}
        />
      ) : (
        <PageQuiz
          cours={cours}
          portee={portee}
          surPortee={setPortee}
          mode={modeQuiz}
          surMode={setModeQuiz}
          user={user}
          surAllerSlide={allerSlide}
          surTestee={(n) => marquer(n, "testee")}
        />
      )}
    </>
  );
}
