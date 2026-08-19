"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { EmptyState, LoadingPanel } from "@/components/ui-states";
import { api, ApiError } from "@/lib/api";
import type { EnvironmentalData, Indicator, NormalizedEntry, QualityAlert, QualitySummary, Site } from "@/lib/types";

const severityStyles = {
  info: "border-sky-200 bg-sky-50 text-sky-700",
  warning: "border-amber-200 bg-amber-50 text-amber-700",
  critical: "border-rose-200 bg-rose-50 text-rose-700",
};

const canNormalize = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement" || role === "consultant";
const canValidate = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement";

function scoreTone(score: number) {
  if (score >= 80) return "text-emerald-700";
  if (score >= 55) return "text-amber-700";
  return "text-rose-700";
}

export default function QualityPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<QualitySummary | null>(null);
  const [entries, setEntries] = useState<EnvironmentalData[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<"all" | "critical" | "warning" | "info">("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [quality, data, siteData, indicatorData] = await Promise.all([
        api.get<QualitySummary>("/quality/summary"),
        api.get<EnvironmentalData[]>("/data"),
        api.get<Site[]>("/sites"),
        api.get<Indicator[]>("/reference/indicators"),
      ]);
      setSummary(quality);
      setEntries(data);
      setSites(siteData);
      setIndicators(indicatorData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger la qualité des données.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const alertByDataId = useMemo(() => {
    const map = new Map<number, QualityAlert[]>();
    for (const alert of summary?.alerts ?? []) {
      map.set(alert.data_id, [...(map.get(alert.data_id) ?? []), alert]);
    }
    return map;
  }, [summary]);
  const filteredAlerts = useMemo(() => {
    const alerts = summary?.alerts ?? [];
    if (severityFilter === "all") return alerts;
    return alerts.filter((alert) => alert.severity === severityFilter);
  }, [severityFilter, summary]);

  async function normalize(entry: EnvironmentalData) {
    setBusyId(entry.id);
    setError(null);
    setMessage(null);
    try {
      const result = await api.post<NormalizedEntry>(`/quality/data/${entry.id}/normalize`);
      setMessage(`Donnée #${result.data_id} normalisée: ${result.normalized_value} ${result.normalized_unit}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Normalisation impossible.");
    } finally {
      setBusyId(null);
    }
  }

  async function validate(entry: EnvironmentalData) {
    setBusyId(entry.id);
    setError(null);
    setMessage(null);
    try {
      await api.post<EnvironmentalData>(`/quality/data/${entry.id}/validate`);
      setMessage(`Donnée #${entry.id} validée après contrôle qualité.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Validation impossible.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Gouvernance des données</p>
            <h1 className="text-2xl font-bold text-slate-950">Qualité et normalisation</h1>
            <p className="mt-1 text-sm text-slate-500">
              Contrôlez les valeurs manquantes, les unités, les doublons et les anomalies avant validation.
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-5 py-4 text-right shadow-sm">
            <p className="text-xs uppercase tracking-wide text-slate-400">Score qualité</p>
            <p className={`text-3xl font-bold ${scoreTone(summary?.quality_score ?? 0)}`}>
              {summary?.quality_score ?? "--"}%
            </p>
          </div>
        </div>

        {error ? <p className="mt-6 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
        {message ? <p className="mt-6 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

        {loading ? (
          <div className="mt-6">
            <LoadingPanel label="Analyse qualité en cours..." />
          </div>
        ) : null}

        {!loading ? <section className="mt-6 grid gap-4 md:grid-cols-4">
          {[
            ["Données", summary?.total_entries ?? 0],
            ["Brouillons", summary?.draft_entries ?? 0],
            ["Validées", summary?.valid_entries ?? 0],
            ["Alertes", summary?.alerts.length ?? 0],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
            </div>
          ))}
        </section> : null}

        {!loading ? <section className="mt-6 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-semibold text-slate-950">Alertes qualité</h2>
              <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-1">
                {[
                  ["all", "Toutes"],
                  ["critical", "Critiques"],
                  ["warning", "Avert."],
                  ["info", "Info"],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setSeverityFilter(value as "all" | "critical" | "warning" | "info")}
                    className={`rounded-md px-2.5 py-1 text-xs font-semibold ${
                      severityFilter === value ? "bg-white text-teal-700 shadow-sm" : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-4 space-y-3">
              {filteredAlerts.slice(0, 8).map((alert) => (
                <div key={alert.id} className={`rounded-lg border p-3 ${severityStyles[alert.severity]}`}>
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-semibold">{alert.title}</p>
                    <span className="text-xs uppercase">{alert.severity}</span>
                  </div>
                  <p className="mt-1 text-sm">{alert.message}</p>
                  <p className="mt-2 text-xs">{alert.recommendation}</p>
                </div>
              ))}
              {!loading && filteredAlerts.length === 0 ? (
                <EmptyState title="Aucune alerte dans ce filtre" description="Les données visibles ne nécessitent pas d'action pour cette gravité." />
              ) : null}
            </div>
          </div>

          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-4 py-3">
              <h2 className="font-semibold text-slate-950">Workflow de validation</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Date</th>
                    <th className="px-4 py-3 font-semibold">Site</th>
                    <th className="px-4 py-3 font-semibold">Indicateur</th>
                    <th className="px-4 py-3 font-semibold">Valeur</th>
                    <th className="px-4 py-3 font-semibold">État</th>
                    <th className="px-4 py-3 font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {entries.slice(0, 12).map((entry) => {
                    const alerts = alertByDataId.get(entry.id) ?? [];
                    return (
                      <tr key={entry.id} className="hover:bg-slate-50">
                        <td className="whitespace-nowrap px-4 py-3 text-slate-500">{entry.entry_date}</td>
                        <td className="px-4 py-3 text-slate-700">{sites.find((site) => site.id === entry.site_id)?.name ?? "A compléter"}</td>
                        <td className="px-4 py-3 text-slate-700">{indicators.find((indicator) => indicator.id === entry.indicator_id)?.name ?? "A compléter"}</td>
                        <td className="px-4 py-3 font-medium text-slate-950">{entry.value} {entry.unit}</td>
                        <td className="px-4 py-3">
                          {alerts.length ? (
                            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">{alerts.length} alerte(s)</span>
                          ) : (
                            <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">Prêt</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            {canNormalize(user?.role) && entry.status === "brouillon" ? (
                              <button type="button" onClick={() => normalize(entry)} disabled={busyId === entry.id} className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50">
                                Normaliser
                              </button>
                            ) : null}
                            {canValidate(user?.role) && entry.status === "brouillon" ? (
                              <button type="button" onClick={() => validate(entry)} disabled={busyId === entry.id} className="rounded-lg bg-slate-950 px-3 py-1 text-xs font-semibold text-white hover:bg-slate-700 disabled:opacity-50">
                                Valider
                              </button>
                            ) : null}
                            {entry.status === "valide" ? <span className="text-xs text-slate-400">Validé</span> : null}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {!loading && entries.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-4">
                        <EmptyState title="Aucune donnée à contrôler" description="Ajoutez ou importez une donnée pour démarrer le workflow qualité." action="Ajouter une donnée" href="/dashboard/entry" />
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </section> : null}
      </main>
    </>
  );
}
