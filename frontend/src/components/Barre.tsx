// Barre du haut des maquettes : marque, cours actuel, import PDF/PPTX, onglets Cours/Quiz, langues.
import { useRef, useState } from "react";
import { api, ErreurApi } from "../api";
import { useLangue } from "../i18n";
import type { Course, LangueUI } from "../types";
import { Icone } from "./Icones";

export type Page = "cours" | "quiz";

interface Props {
  cours: Course | null;
  page: Page;
  surPage: (p: Page) => void;
  surCours: (c: Course) => void;
  surErreur: (message: string) => void;
}

export function Barre({ cours, page, surPage, surCours, surErreur }: Props) {
  const { t, langue, setLangue } = useLangue();

  return (
    <header className="barre">
      <a
        className="marque"
        href="#cours"
        aria-label="Multi-Agent Tutor"
        onClick={(e) => {
          e.preventDefault();
          surPage("cours");
        }}
      >
        <img src="/img/logo-icone.png" alt="" width={44} height={44} />
        <span className="marque-nom">
          Multi-Agent <b>Tutor</b>
        </span>
      </a>
      {cours && (
        <div className="cours-actuel">
          <Icone nom="livre" />
          <strong title={cours.fichier_source}>{cours.titre}</strong>
        </div>
      )}
      <Televersement surCours={surCours} surErreur={surErreur} compact />
      {cours && (
        <nav className="onglets" aria-label="Sections">
          {(["cours", "quiz"] as const).map((p) => (
            <a
              key={p}
              href={`#${p}`}
              aria-current={page === p ? "page" : undefined}
              onClick={(e) => {
                e.preventDefault();
                surPage(p);
              }}
            >
              <Icone nom={p} />
              <span>{t(p)}</span>
            </a>
          ))}
        </nav>
      )}
      <div className="langues" role="group" aria-label="Langue" style={cours ? undefined : { marginInlineStart: "auto" }}>
        {(["fr", "en", "ar"] as LangueUI[]).map((l) => (
          <button
            key={l}
            type="button"
            aria-pressed={langue === l}
            aria-label={l === "ar" ? "العربية" : undefined}
            onClick={() => setLangue(l)}
          >
            {l.toUpperCase()}
          </button>
        ))}
      </div>
    </header>
  );
}

/** Import d'un support PDF/PPTX via POST /upload. */
export function Televersement({
  surCours,
  surErreur,
  compact = false,
}: {
  surCours: (c: Course) => void;
  surErreur: (message: string) => void;
  compact?: boolean;
}) {
  const { t } = useLangue();
  const champ = useRef<HTMLInputElement>(null);
  const [enCours, setEnCours] = useState(false);

  async function envoyer(fichier: File | undefined) {
    if (!fichier) return;
    if (!/\.(pdf|pptx)$/i.test(fichier.name)) {
      surErreur(`${fichier.name} : ${t("importer-aide")}`);
      return;
    }
    setEnCours(true);
    try {
      surCours(await api.televerser(fichier));
    } catch (e) {
      surErreur(e instanceof ErreurApi ? e.message : String(e));
    } finally {
      setEnCours(false);
      if (champ.current) champ.current.value = "";
    }
  }

  return (
    <>
      <input
        ref={champ}
        type="file"
        accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation"
        hidden
        onChange={(e) => envoyer(e.target.files?.[0])}
      />
      <button
        type="button"
        className={compact ? "bouton discret importer" : "bouton principal"}
        disabled={enCours}
        onClick={() => champ.current?.click()}
        title={t("importer-aide")}
      >
        <Icone nom="importer" />
        <span>{enCours ? t("import") : t("importer")}</span>
      </button>
    </>
  );
}
