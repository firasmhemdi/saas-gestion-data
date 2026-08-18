"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";

const helpByRoute = [
  {
    match: "/dashboard/analytics",
    title: "Piloter les indicateurs ESG",
    description: "Analysez les consommations, les émissions par scope et les écarts entre sites.",
    actions: [
      ["Exporter le rapport", "/dashboard/analytics"],
      ["Vérifier la qualité", "/dashboard/quality"],
      ["Questionner l'assistant", "/dashboard/assistant"],
    ],
  },
  {
    match: "/dashboard/quality",
    title: "Fiabiliser les données",
    description: "Traitez d'abord les alertes critiques, normalisez les unités, puis validez.",
    actions: [
      ["Filtrer les critiques", "/dashboard/quality"],
      ["Ajouter une donnée", "/dashboard/entry"],
      ["Voir l'impact ESG", "/dashboard/analytics"],
    ],
  },
  {
    match: "/dashboard/assistant",
    title: "Interroger les données",
    description: "Posez une question métier et vérifiez toujours les sources citées.",
    actions: [
      ["Voir le dashboard", "/dashboard/analytics"],
      ["Contrôler les sources", "/dashboard/documents"],
      ["Consulter l'audit", "/dashboard/audit"],
    ],
  },
  {
    match: "/dashboard/documents",
    title: "Transformer les documents",
    description: "Déposez un document, corrigez les champs extraits, puis intégrez la donnée.",
    actions: [
      ["Valider l'extraction", "/dashboard/documents"],
      ["Contrôler la qualité", "/dashboard/quality"],
      ["Voir les données", "/dashboard/entry"],
    ],
  },
  {
    match: "/dashboard",
    title: "Parcours recommandé",
    description: "Présentez l'app de bout en bout: collecte, qualité, analytics puis assistant IA.",
    actions: [
      ["Commencer la démo", "/dashboard/entry"],
      ["Mode présentation", "/dashboard"],
      ["Recherche rapide", "/dashboard"],
    ],
  },
];

function currentHelp(pathname: string) {
  return helpByRoute.find((item) => pathname.startsWith(item.match) && item.match !== "/dashboard") ?? helpByRoute[4];
}

export function ContextualHelp() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const help = useMemo(() => currentHelp(pathname), [pathname]);

  return (
    <div className="fixed bottom-4 right-4 z-40">
      {open ? (
        <div className="mb-3 w-[min(360px,calc(100vw-32px))] rounded-lg border border-slate-200 bg-white p-4 shadow-2xl">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Aide contextuelle</p>
              <h2 className="mt-1 font-semibold text-slate-950">{help.title}</h2>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-500 hover:bg-slate-50"
            >
              Fermer
            </button>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-500">{help.description}</p>
          <div className="mt-4 grid gap-2">
            {help.actions.map(([label, href]) => (
              <Link key={label} href={href} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-800">
                {label}
              </Link>
            ))}
          </div>
          <div className="mt-4 rounded-lg bg-slate-950 px-3 py-2 text-xs leading-5 text-slate-200">
            Utilisez <span className="font-semibold text-white">Ctrl K</span> pour rechercher rapidement un module.
          </div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="rounded-lg bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-xl transition hover:bg-slate-700"
      >
        Aide
      </button>
    </div>
  );
}
