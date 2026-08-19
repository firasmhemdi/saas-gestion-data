"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const modules = [
  { title: "Dashboard ESG", href: "/dashboard/analytics", group: "Pilotage", keywords: "kpi scope carbone émissions analytics indicateurs" },
  { title: "Qualité des données", href: "/dashboard/quality", group: "Fiabilité", keywords: "alertes normalisation validation anomalies doublons" },
  { title: "Assistant IA", href: "/dashboard/assistant", group: "Restitution", keywords: "question rag source historique ia" },
  { title: "Documents OCR/NLP", href: "/dashboard/documents", group: "Collecte", keywords: "facture bordereau extraction validation document" },
  { title: "Saisie manuelle", href: "/dashboard/entry", group: "Collecte", keywords: "donnée valeur site indicateur" },
  { title: "Imports", href: "/dashboard/imports", group: "Collecte", keywords: "csv excel aperçu traitement" },
  { title: "Mapping ERP", href: "/dashboard/mapping", group: "Intégration", keywords: "mapping source connecteur synchronisation" },
  { title: "Référentiel", href: "/dashboard/reference", group: "Administration", keywords: "indicateur facteur émission unité" },
  { title: "Sites", href: "/dashboard/sites", group: "Administration", keywords: "usine site localisation tenant" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const results = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return modules;
    return modules.filter((item) => `${item.title} ${item.group} ${item.keywords}`.toLowerCase().includes(term));
  }, [query]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="hidden h-10 items-center rounded-xl border border-white/10 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline-emerald-300 md:inline-flex 2xl:px-3.5"
      >
        Rechercher
        <span className="ml-2 hidden rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500 2xl:inline">Ctrl K</span>
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 bg-slate-950/35 px-4 py-20 backdrop-blur-sm" onMouseDown={() => setOpen(false)}>
          <div className="mx-auto max-w-xl overflow-hidden rounded-lg bg-white shadow-2xl" onMouseDown={(event) => event.stopPropagation()}>
            <div className="border-b border-slate-200 p-4">
              <label htmlFor="command-search" className="sr-only">Rechercher un module</label>
              <input
                id="command-search"
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Rechercher: qualité, carbone, document..."
                className="w-full rounded-lg border border-slate-300 px-3 py-3 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              />
            </div>
            <div className="max-h-[420px] overflow-y-auto p-2">
              {results.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="block rounded-lg px-3 py-3 transition hover:bg-teal-50"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-950">{item.title}</p>
                      <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-400">{item.group}</p>
                    </div>
                    <span className="text-sm font-semibold text-teal-700">Ouvrir</span>
                  </div>
                </Link>
              ))}
              {results.length === 0 ? (
                <p className="px-3 py-8 text-center text-sm text-slate-500">Aucun module trouvé.</p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
