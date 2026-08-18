"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { api, ApiError } from "@/lib/api";
import type { EnvironmentalData, EnvironmentalDataPayload, Indicator, Site } from "@/lib/types";

const canWrite = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement" || role === "consultant";
const canValidate = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement";

function EntryForm({
  sites,
  indicators,
  onDone,
}: {
  sites: Site[];
  indicators: Indicator[];
  onDone: () => Promise<void>;
}) {
  const [siteId, setSiteId] = useState("");
  const [indicatorId, setIndicatorId] = useState("");
  const [entryDate, setEntryDate] = useState(new Date().toISOString().slice(0, 10));
  const [value, setValue] = useState("");
  const [unit, setUnit] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: EnvironmentalDataPayload = {
        site_id: siteId ? Number(siteId) : null,
        indicator_id: indicatorId ? Number(indicatorId) : null,
        entry_date: entryDate,
        value: Number(value),
        unit,
        source: "manuel",
      };
      await api.post<EnvironmentalData>("/data", payload);
      setValue("");
      setUnit("");
      setSiteId("");
      setIndicatorId("");
      await onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-3">
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">Site</label>
        <select value={siteId} onChange={(e) => setSiteId(e.target.value)} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
          <option value="">Sans site</option>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">Indicateur</label>
        <select value={indicatorId} onChange={(e) => setIndicatorId(e.target.value)} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
          <option value="">Sans indicateur</option>
          {indicators.map((ind) => (
            <option key={ind.id} value={ind.id}>
              {ind.name} ({ind.unit})
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">Date</label>
        <input type="date" required value={entryDate} onChange={(e) => setEntryDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">Valeur</label>
        <input type="number" step="any" required value={value} onChange={(e) => setValue(e.target.value)} placeholder="1234.5" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      </div>
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-500">Unité</label>
        <input required value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="kWh" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      </div>
      <div className="flex items-end">
        <button type="submit" disabled={submitting} className="w-full rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60">
          {submitting ? "Enregistrement…" : "Saisir la donnée"}
        </button>
      </div>
      {error ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-3">{error}</p> : null}
    </form>
  );
}

export default function EntryPage() {
  const { user: currentUser } = useAuth();
  const [entries, setEntries] = useState<EnvironmentalData[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, sitesData, indicatorsData] = await Promise.all([
        api.get<EnvironmentalData[]>("/data"),
        api.get<Site[]>("/sites"),
        api.get<Indicator[]>("/reference/indicators"),
      ]);
      setEntries(data);
      setSites(sitesData);
      setIndicators(indicatorsData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les données.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const writer = canWrite(currentUser?.role);
  const validator = canValidate(currentUser?.role);

  async function validate(entry: EnvironmentalData) {
    try {
      await api.post<EnvironmentalData>(`/data/${entry.id}/validate`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de valider la donnée.");
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Saisie manuelle des données</h1>
          <p className="mt-1 text-sm text-slate-500">
            Complétez le référentiel : les données saisies sont enregistrées en brouillon puis validées.
          </p>
        </div>

        {writer ? (
          <div className="mt-6">
            <EntryForm sites={sites} indicators={indicators} onDone={load} />
          </div>
        ) : null}

        {error ? (
          <p className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        ) : null}

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Chargement…</p>
        ) : (
          <div className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Date</th>
                  <th className="px-4 py-3 font-semibold">Site</th>
                  <th className="px-4 py-3 font-semibold">Indicateur</th>
                  <th className="px-4 py-3 font-semibold">Valeur</th>
                  <th className="px-4 py-3 font-semibold">Statut</th>
                  {validator ? <th className="px-4 py-3 font-semibold">Validation</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-4 py-3 text-slate-500">{entry.entry_date}</td>
                    <td className="px-4 py-3 text-slate-700">
                      {sites.find((s) => s.id === entry.site_id)?.name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {indicators.find((i) => i.id === entry.indicator_id)?.name ?? "—"}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {entry.value} {entry.unit}
                    </td>
                    <td className="px-4 py-3">
                      {entry.status === "valide" ? (
                        <span className="inline-flex rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                          Validé
                        </span>
                      ) : (
                        <span className="inline-flex rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
                          Brouillon
                        </span>
                      )}
                    </td>
                    {validator ? (
                      <td className="px-4 py-3">
                        {entry.status === "brouillon" ? (
                          <button
                            type="button"
                            onClick={() => validate(entry)}
                            className="rounded-lg border border-emerald-300 px-3 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50"
                          >
                            Valider
                          </button>
                        ) : (
                          <span className="text-xs text-slate-300">—</span>
                        )}
                      </td>
                    ) : null}
                  </tr>
                ))}
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      Aucune donnée saisie pour le moment.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
