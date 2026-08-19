import Link from "next/link";

import { ProductShowcase } from "@/components/product-showcase";

const proofPoints = [
  ["360°", "cycle donnée ESG"],
  ["12+", "fonctions métier"],
  ["3", "scopes carbone"],
];

export default function Home() {
  return (
    <main className="min-h-screen text-slate-950">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-700 text-sm font-bold text-white">
              SG
            </div>
            <div>
              <p className="font-semibold leading-tight">SaaS Gestion Data</p>
              <p className="text-xs text-slate-500">Environmental Data Platform</p>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <Link href="/login" className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100">
              Connexion
            </Link>
            <Link href="/register" className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700">
              Créer un compte
            </Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto grid min-h-[calc(100vh-73px)] max-w-7xl items-center gap-10 px-4 py-10 lg:grid-cols-[0.95fr_1.05fr]">
        <div>
          <p className="inline-flex rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-800">
            Plateforme ESG pour entreprises multi-sites
          </p>
          <h1 className="mt-5 max-w-3xl text-4xl font-bold leading-tight tracking-tight text-slate-950 md:text-5xl">
            Centraliser, contrôler et valoriser les données environnementales d&apos;une entreprise.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
            Une application SaaS multi-tenant qui couvre le cycle complet : collecte, contrôle qualité,
            documents OCR, reporting ESG et assistant IA avec réponses sourcées.
          </p>

          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <Link href="/register" className="rounded-lg bg-teal-700 px-5 py-3 text-center text-sm font-semibold text-white shadow-sm hover:bg-teal-800">
              Créer un espace
            </Link>
            <Link href="/login" className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-center text-sm font-semibold text-slate-700 hover:bg-slate-50">
              Accéder au cockpit
            </Link>
          </div>

          <div className="mt-9 grid max-w-xl grid-cols-3 gap-3">
            {proofPoints.map(([value, label]) => (
              <div key={label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-2xl font-bold text-slate-950">{value}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <ProductShowcase />
      </section>
    </main>
  );
}
