"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { EmptyState, LoadingPanel } from "@/components/ui-states";
import { api, ApiError } from "@/lib/api";
import type { AnalyticsSummary } from "@/lib/types";

function formatValue(value: number) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(value);
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSummary(await api.get<AnalyticsSummary>("/analytics/summary"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les indicateurs ESG.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const maxEmission = useMemo(
    () => Math.max(1, ...(summary?.site_performance ?? []).map((site) => site.emissions_kgco2e)),
    [summary],
  );
  const maxScope = useMemo(
    () => Math.max(1, ...(summary?.emissions_by_scope ?? []).map((scope) => scope.value)),
    [summary],
  );

  function exportReport() {
    if (!summary) return;
    const rows = [
      ["Section", "Libellé", "Valeur", "Unité"],
      ...summary.metrics.map((metric) => ["KPI", metric.label, String(metric.value), metric.unit]),
      ...summary.emissions_by_scope.map((scope) => ["Scope carbone", `Scope ${scope.scope}`, String(scope.value), scope.unit]),
      ...summary.site_performance.map((site) => ["Site", site.site_name, String(site.emissions_kgco2e), "kgCO2e"]),
    ];
    const csv = rows.map((row) => row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(";")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "rapport-esg.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Sprint 7</p>
            <h1 className="text-2xl font-bold text-slate-950">Dashboard ESG</h1>
            <p className="mt-1 text-sm text-slate-500">
              Suivez les consommations, déchets et émissions carbone par site et par scope.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={exportReport} disabled={!summary} className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50">
              Exporter CSV
            </button>
            <button type="button" onClick={load} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              Actualiser
            </button>
          </div>
        </div>

        {error ? <p className="mt-6 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

        {loading ? (
          <div className="mt-6">
            <LoadingPanel label="Préparation des indicateurs ESG..." />
          </div>
        ) : null}

        {!loading ? <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {(summary?.metrics ?? []).map((metric) => (
            <div key={metric.key} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-400">{metric.label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{formatValue(metric.value)}</p>
              <div className="mt-2 flex items-center justify-between gap-3 text-xs">
                <span className="text-slate-500">{metric.unit}</span>
                <span className={metric.trend <= 0 ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
                  {metric.trend > 0 ? "+" : ""}{metric.trend}%
                </span>
              </div>
            </div>
          ))}
        </section> : null}

        {!loading ? <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_0.85fr]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">Comparaison multi-sites</h2>
            <div className="mt-5 space-y-4">
              {(summary?.site_performance ?? []).map((site) => (
                <div key={site.site_id ?? "none"}>
                  <div className="flex items-center justify-between gap-4 text-sm">
                    <p className="font-medium text-slate-900">{site.site_name}</p>
                    <p className="text-slate-500">{formatValue(site.emissions_kgco2e)} kgCO2e</p>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-teal-600" style={{ width: `${Math.max(4, (site.emissions_kgco2e / maxEmission) * 100)}%` }} />
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-500">
                    <span>{formatValue(site.energy_kwh)} kWh</span>
                    <span>{formatValue(site.water_m3)} m3</span>
                    <span>{formatValue(site.waste_tonnes)} t</span>
                  </div>
                </div>
              ))}
              {!loading && summary?.site_performance.length === 0 ? (
                <EmptyState title="Aucun site à comparer" description="Ajoutez des sites et validez des données environnementales pour alimenter ce tableau." action="Ajouter une donnée" href="/dashboard/entry" />
              ) : null}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">Émissions par scope</h2>
            <div className="mt-5 space-y-4">
              {(summary?.emissions_by_scope ?? []).map((scope) => (
                <div key={scope.scope}>
                  <div className="flex items-center justify-between text-sm">
                    <p className="font-medium text-slate-900">Scope {scope.scope}</p>
                    <p className="text-slate-500">{formatValue(scope.value)} {scope.unit}</p>
                  </div>
                  <div className="mt-2 h-8 overflow-hidden rounded-lg bg-slate-100">
                    <div className="flex h-full items-center justify-end rounded-lg bg-slate-900 pr-3 text-xs font-semibold text-white" style={{ width: `${Math.max(8, (scope.value / maxScope) * 100)}%` }}>
                      {formatValue(scope.value)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section> : null}

        {!loading ? <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-slate-950">Totaux par famille d&apos;indicateurs</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {(summary?.categories ?? []).map((category) => (
              <div key={`${category.category}-${category.unit}`} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-medium text-slate-700">{category.label}</p>
                <p className="mt-2 text-xl font-bold text-slate-950">{formatValue(category.value)} {category.unit}</p>
              </div>
            ))}
            {!loading && summary?.categories.length === 0 ? (
              <EmptyState title="Aucun total disponible" description="Les totaux apparaîtront dès que des indicateurs et données validées seront présents." action="Ouvrir le référentiel" href="/dashboard/reference" />
            ) : null}
          </div>
        </section> : null}
      </main>
    </>
  );
}
