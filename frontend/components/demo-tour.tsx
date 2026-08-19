"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "sgd_onboarding_tour_completed";

const steps = [
  {
    title: "Collecter une donnée",
    description: "Saisie, import ou document : faites entrer une donnée fiable dans le système.",
    href: "/dashboard/entry",
  },
  {
    title: "Contrôler la qualité",
    description: "Filtrez les alertes, normalisez les unités et validez les lignes fiables.",
    href: "/dashboard/quality",
  },
  {
    title: "Piloter les KPI ESG",
    description: "Présentez les consommations, émissions par scope et comparaisons multi-sites.",
    href: "/dashboard/analytics",
  },
  {
    title: "Interroger l'assistant IA",
    description: "Posez une question métier et vérifiez les sources utilisées dans la réponse.",
    href: "/dashboard/assistant",
  },
];

export function DemoTour() {
  const [completed, setCompleted] = useState<number[]>([]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) setCompleted(JSON.parse(saved));
    } catch {
      setCompleted([]);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(completed));
  }, [completed]);

  const progress = useMemo(() => Math.round((completed.length / steps.length) * 100), [completed.length]);

  function toggle(index: number) {
    setCompleted((current) =>
      current.includes(index) ? current.filter((item) => item !== index) : [...current, index],
    );
  }

  function reset() {
    setCompleted([]);
  }

  return (
    <div className="app-surface rounded-lg p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Prise en main</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Parcours guidé</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Suivez ces étapes pour présenter un flux complet, clair et convaincant.
          </p>
        </div>
        <button
          type="button"
          onClick={reset}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
        >
          Réinitialiser
        </button>
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
          <span>Progression du parcours</span>
          <span>{progress}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="metric-bar h-full rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        {steps.map((step, index) => {
          const done = completed.includes(index);
          return (
            <div key={step.title} className={`rounded-lg border p-4 transition ${done ? "border-teal-200 bg-teal-50" : "border-slate-200 bg-white"}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <button type="button" onClick={() => toggle(index)} className="flex min-w-0 flex-1 items-start gap-3 text-left">
                  <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold ${done ? "border-teal-700 bg-teal-700 text-white" : "border-slate-300 text-slate-500"}`}>
                    {done ? "✓" : index + 1}
                  </span>
                  <span>
                    <span className="block font-semibold text-slate-950">{step.title}</span>
                    <span className="mt-1 block text-sm leading-6 text-slate-500">{step.description}</span>
                  </span>
                </button>
                <Link href={step.href} className="rounded-lg bg-slate-950 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700">
                  Ouvrir
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
