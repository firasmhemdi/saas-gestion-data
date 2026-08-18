"use client";

import { useState } from "react";

const views = [
  {
    key: "collecte",
    title: "Collecte multi-source",
    caption: "Excel, ERP, API, documents et saisie manuelle réunis dans un même flux.",
    stats: [["Sources", "5"], ["Imports", "128"], ["Succès", "96%"]],
    rows: ["Facture énergie détectée", "Mapping ELEC_CONS appliqué", "Synchronisation ERP terminée"],
  },
  {
    key: "qualite",
    title: "Qualité et validation",
    caption: "Les anomalies sont détectées avant intégration dans le référentiel officiel.",
    stats: [["Score", "92%"], ["Alertes", "4"], ["Validées", "312"]],
    rows: ["Unité MWh normalisée en kWh", "Doublon probable isolé", "Valeur aberrante à vérifier"],
  },
  {
    key: "analytics",
    title: "Pilotage ESG",
    caption: "Les responsables suivent consommations, déchets et émissions carbone par site.",
    stats: [["Énergie", "48k"], ["Scope 2", "20t"], ["Sites", "7"]],
    rows: ["Usine Tunis en tête des émissions", "Eau en baisse sur Sfax", "Rapport ESG exporté"],
  },
  {
    key: "assistant",
    title: "Assistant IA sourcé",
    caption: "Les questions métier obtiennent une réponse traçable avec sources internes.",
    stats: [["Questions", "42"], ["Sources", "118"], ["Temps", "2s"]],
    rows: ["Quel site consomme le plus ?", "Réponse citant site + période", "Historique enregistré"],
  },
];

export function ProductShowcase() {
  const [active, setActive] = useState(views[0]);

  return (
    <div className="glass-surface rounded-lg p-4">
      <div className="rounded-lg border border-slate-200 bg-slate-950 p-4 text-white shadow-2xl">
        <div className="flex flex-wrap gap-2">
          {views.map((view) => (
            <button
              key={view.key}
              type="button"
              onClick={() => setActive(view)}
              className={`rounded-lg px-3 py-2 text-xs font-semibold transition ${
                active.key === view.key ? "bg-teal-400 text-slate-950" : "bg-white/10 text-slate-200 hover:bg-white/15"
              }`}
            >
              {view.title}
            </button>
          ))}
        </div>

        <div className="mt-5 border-b border-white/10 pb-4">
          <p className="text-xs uppercase tracking-wide text-teal-200">Aperçu interactif</p>
          <h2 className="mt-1 text-xl font-semibold">{active.title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">{active.caption}</p>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {active.stats.map(([label, value]) => (
            <div key={label} className="rounded-lg bg-white/10 p-4">
              <p className="text-xs text-slate-300">{label}</p>
              <p className="mt-2 text-lg font-bold">{value}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded-lg bg-white p-4 text-slate-950">
          <div className="flex items-center justify-between text-sm">
            <p className="font-semibold">Activité récente</p>
            <span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700">Live</span>
          </div>
          <div className="mt-4 space-y-3">
            {active.rows.map((row, index) => (
              <div key={row} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-950 text-xs font-semibold text-white">
                  {index + 1}
                </span>
                <p className="text-sm font-medium text-slate-700">{row}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
