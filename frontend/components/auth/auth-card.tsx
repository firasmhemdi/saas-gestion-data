export function AuthCard({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen overflow-x-hidden bg-slate-50 px-4 py-6 lg:px-6 lg:py-8">
      <div className="mx-auto grid min-h-[calc(100vh-64px)] w-full max-w-[1440px] gap-6 lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,1.05fr)]">
        <section className="hidden min-w-0 overflow-hidden rounded-lg bg-slate-950 p-6 text-white shadow-2xl lg:flex lg:flex-col lg:justify-between xl:p-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-teal-500 text-sm font-bold text-white">
                SG
              </div>
              <div className="min-w-0">
                <p className="font-semibold">SaaS Gestion Data</p>
                <p className="text-xs text-slate-300">Plateforme ESG multi-tenant</p>
              </div>
            </div>
            <div className="mt-12 max-w-xl xl:mt-14">
              <p className="text-xs font-semibold uppercase tracking-wide text-teal-200">Du document au reporting</p>
              <h1 className="mt-3 text-3xl font-bold leading-tight xl:text-4xl">
                Une expérience claire pour collecter, fiabiliser et exploiter les données environnementales.
              </h1>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                Connecteurs, documents, qualité, indicateurs ESG et assistant IA sont pensés comme un seul parcours.
              </p>
            </div>
          </div>
          <div className="grid gap-3">
            {[
              ["Qualité", "Alertes, normalisation et validation avant intégration."],
              ["Analytics", "KPI ESG, scopes carbone et comparaison multi-sites."],
              ["Assistant IA", "Réponses sourcées sur les données internes."],
            ].map(([title, description]) => (
              <div key={title} className="rounded-lg border border-white/10 bg-white/10 p-4">
                <p className="font-semibold">{title}</p>
                <p className="mt-1 text-xs leading-5 text-slate-300">{description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="flex min-w-0 items-center justify-center py-4 lg:py-0">
          <div className="w-full max-w-md">
            <div className="mb-8 text-center lg:hidden">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-teal-700 text-xl font-bold text-white">
                SG
              </div>
              <h1 className="text-2xl font-bold text-slate-900">SaaS Gestion Data</h1>
              <p className="mt-1 text-sm text-slate-500">
                Plateforme de gestion des données environnementales
              </p>
            </div>
            <div className="app-surface rounded-lg p-8">{children}</div>
          </div>
        </section>
      </div>
    </main>
  );
}
