"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { api, ApiError } from "@/lib/api";
import type { DataMapping, DataSource, SyncSchedule } from "@/lib/types";

const defaultRules = '{\n  "product_qty": "value",\n  "invoice_date": "entry_date",\n  "uom": "unit"\n}';

function parseRules(raw: string): Record<string, string> {
  const parsed = JSON.parse(raw);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Le mapping doit être un objet JSON.");
  return parsed as Record<string, string>;
}

export default function MappingPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [mappings, setMappings] = useState<DataMapping[]>([]);
  const [schedules, setSchedules] = useState<SyncSchedule[]>([]);
  const [name, setName] = useState("Mapping ERP Odoo");
  const [sourceId, setSourceId] = useState("");
  const [rules, setRules] = useState(defaultRules);
  const [frequency, setFrequency] = useState("daily");
  const [windowStart, setWindowStart] = useState("22:00");
  const [windowEnd, setWindowEnd] = useState("23:00");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [sourceData, mappingData, scheduleData] = await Promise.all([
        api.get<DataSource[]>("/data-sources"),
        api.get<DataMapping[]>("/mappings"),
        api.get<SyncSchedule[]>("/sync-schedules"),
      ]);
      setSources(sourceData);
      setMappings(mappingData);
      setSchedules(scheduleData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger la configuration.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function saveMapping(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await api.post<DataMapping>("/mappings", {
        name,
        source_id: sourceId ? Number(sourceId) : null,
        target_model: "environmental_data",
        rules: parseRules(rules),
      });
      setMessage("Mapping enregistré.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'enregistrer le mapping.");
    } finally {
      setBusy(false);
    }
  }

  async function createSchedule(event: React.FormEvent) {
    event.preventDefault();
    if (!sourceId) {
      setError("Choisissez une source à synchroniser.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await api.post<SyncSchedule>("/sync-schedules", {
        source_id: Number(sourceId),
        frequency,
        window_start: windowStart,
        window_end: windowEnd,
        is_active: true,
      });
      setMessage("Planification créée.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de créer la planification.");
    } finally {
      setBusy(false);
    }
  }

  async function runSync(id: number) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await api.post<{ ok: boolean; message: string; import_id: number }>(`/data-sources/${id}/sync`);
      setMessage(`${result.message} Import #${result.import_id}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de lancer la synchronisation.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div>
          <p className="text-xs font-semibold uppercase text-emerald-700">Intégration des sources</p>
          <h1 className="text-2xl font-bold text-slate-950">ERP, data mapping et synchronisation</h1>
          <p className="mt-1 text-sm text-slate-500">Configurez les correspondances de champs, planifiez les synchronisations et lancez un test lecture seule.</p>
        </div>

        {error ? <p className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        {message ? <p className="mt-6 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

        <section className="mt-6 grid gap-4 lg:grid-cols-2">
          <form onSubmit={saveMapping} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">Mapping source vers modèle</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                Nom
                <input value={name} onChange={(e) => setName(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Source
                <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="">Générique</option>
                  {sources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}
                </select>
              </label>
            </div>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Règles JSON
              <textarea value={rules} onChange={(e) => setRules(e.target.value)} rows={7} spellCheck={false} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs" />
            </label>
            <button disabled={busy} className="mt-4 rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60">
              Enregistrer le mapping
            </button>
          </form>

          <form onSubmit={createSchedule} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">Planification</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                Fréquence
                <select value={frequency} onChange={(e) => setFrequency(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="hourly">Horaire</option>
                  <option value="daily">Quotidienne</option>
                  <option value="weekly">Hebdomadaire</option>
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Source
                <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="">Choisir</option>
                  {sources.filter((source) => ["api", "sql", "erp"].includes(source.source_type)).map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Début
                <input value={windowStart} onChange={(e) => setWindowStart(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Fin
                <input value={windowEnd} onChange={(e) => setWindowEnd(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button disabled={busy} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">
                Créer la planification
              </button>
              {sourceId ? (
                <button type="button" onClick={() => runSync(Number(sourceId))} disabled={busy} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-60">
                  Tester la sync
                </button>
              ) : null}
            </div>
          </form>
        </section>

        <section className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-4 py-3"><h2 className="font-semibold text-slate-950">Mappings enregistrés</h2></div>
            <div className="divide-y divide-slate-100">
              {mappings.map((mapping) => (
                <div key={mapping.id} className="px-4 py-3">
                  <p className="font-medium text-slate-900">{mapping.name}</p>
                  <p className="mt-1 font-mono text-xs text-slate-500">{JSON.stringify(mapping.rules)}</p>
                </div>
              ))}
              {mappings.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-400">Aucun mapping.</p> : null}
            </div>
          </div>

          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-4 py-3"><h2 className="font-semibold text-slate-950">Synchronisations</h2></div>
            <div className="divide-y divide-slate-100">
              {schedules.map((schedule) => (
                <div key={schedule.id} className="flex items-center justify-between gap-3 px-4 py-3">
                  <div>
                    <p className="font-medium text-slate-900">{sources.find((source) => source.id === schedule.source_id)?.name ?? `Source #${schedule.source_id}`}</p>
                    <p className="text-xs text-slate-500">{schedule.frequency} · {schedule.window_start ?? "--"}-{schedule.window_end ?? "--"} · {schedule.last_status}</p>
                  </div>
                  <button type="button" onClick={() => runSync(schedule.source_id)} disabled={busy} className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-60">
                    Lancer
                  </button>
                </div>
              ))}
              {schedules.length === 0 ? <p className="px-4 py-8 text-center text-sm text-slate-400">Aucune planification.</p> : null}
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
