"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { api, ApiError } from "@/lib/api";
import type { DataSource, ImportJob, Indicator, Site } from "@/lib/types";

const targetFields = [
  { key: "entry_date", label: "Date" },
  { key: "value", label: "Valeur" },
  { key: "unit", label: "Unité" },
];

export default function ImportsPage() {
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [filename, setFilename] = useState("consommations.csv");
  const [content, setContent] = useState("date;valeur;unite\n2026-01-15;1234.5;kWh\n2026-01-16;980;kWh");
  const [sourceId, setSourceId] = useState("");
  const [siteId, setSiteId] = useState("");
  const [indicatorId, setIndicatorId] = useState("");
  const [activeJob, setActiveJob] = useState<ImportJob | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const columns = useMemo(() => Object.keys(activeJob?.preview_rows?.[0] ?? {}), [activeJob]);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [jobData, sourceData, siteData, indicatorData] = await Promise.all([
        api.get<ImportJob[]>("/imports"),
        api.get<DataSource[]>("/data-sources"),
        api.get<Site[]>("/sites"),
        api.get<Indicator[]>("/reference/indicators"),
      ]);
      setJobs(jobData);
      setSources(sourceData);
      setSites(siteData);
      setIndicators(indicatorData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les imports.");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function readFile(file: File) {
    setFilename(file.name);
    if (file.name.toLowerCase().endsWith(".xlsx")) {
      const buffer = await file.arrayBuffer();
      const bytes = Array.from(new Uint8Array(buffer), (byte) => String.fromCharCode(byte)).join("");
      setContent(window.btoa(bytes));
      return;
    }
    setContent(await file.text());
  }

  async function preview() {
    setBusy(true);
    setError(null);
    try {
      const job = await api.post<ImportJob>("/imports/preview", {
        filename,
        content,
        source_id: sourceId ? Number(sourceId) : null,
        site_id: siteId ? Number(siteId) : null,
      });
      setActiveJob(job);
      setMapping((job.mapping as Record<string, string>) ?? {});
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de lire le fichier.");
    } finally {
      setBusy(false);
    }
  }

  async function commit() {
    if (!activeJob) return;
    setBusy(true);
    setError(null);
    try {
      const job = await api.post<ImportJob>(`/imports/${activeJob.id}/commit`, {
        mapping,
        site_id: siteId ? Number(siteId) : null,
        indicator_id: indicatorId ? Number(indicatorId) : null,
      });
      setActiveJob(job);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'intégrer les lignes.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase text-emerald-700">Collecte contrôlée</p>
            <h1 className="text-2xl font-bold text-slate-950">Collecte fichiers et traçabilité</h1>
            <p className="mt-1 text-sm text-slate-500">Prévisualisez un CSV/Excel, mappez les colonnes, puis intégrez les données au référentiel.</p>
          </div>
          <button type="button" onClick={preview} disabled={busy || !content} className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60">
            {busy ? "Traitement..." : "Prévisualiser"}
          </button>
        </div>

        {error ? <p className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        <section className="mt-6 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <form className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-medium text-slate-700">
                Fichier
                <input type="file" accept=".csv,.txt,.tsv,.xlsx" onChange={(e) => e.target.files?.[0] && readFile(e.target.files[0])} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Nom
                <input value={filename} onChange={(e) => setFilename(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              </label>
              <label className="text-sm font-medium text-slate-700">
                Source
                <select value={sourceId} onChange={(e) => setSourceId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="">Import manuel</option>
                  {sources.map((source) => <option key={source.id} value={source.id}>{source.name}</option>)}
                </select>
              </label>
              <label className="text-sm font-medium text-slate-700">
                Site
                <select value={siteId} onChange={(e) => setSiteId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="">Aucun</option>
                  {sites.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}
                </select>
              </label>
            </div>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Contenu du fichier
              <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={9} spellCheck={false} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs" />
            </label>
          </form>

          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold text-slate-950">Mapping et aperçu</h2>
              {activeJob ? <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">{activeJob.row_count} ligne(s)</span> : null}
            </div>
            {activeJob ? (
              <>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  {targetFields.map((field) => (
                    <label key={field.key} className="text-sm font-medium text-slate-700">
                      {field.label}
                      <select value={mapping[field.key] ?? ""} onChange={(e) => setMapping({ ...mapping, [field.key]: e.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                        <option value="">Choisir</option>
                        {columns.map((column) => <option key={column} value={column}>{column}</option>)}
                      </select>
                    </label>
                  ))}
                </div>
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Indicateur
                  <select value={indicatorId} onChange={(e) => setIndicatorId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                    <option value="">Non renseigné</option>
                    {indicators.map((indicator) => <option key={indicator.id} value={indicator.id}>{indicator.name}</option>)}
                  </select>
                </label>
                <div className="mt-4 max-h-64 overflow-auto rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-500">
                      <tr>{columns.map((column) => <th key={column} className="px-3 py-2 font-semibold">{column}</th>)}</tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {activeJob.preview_rows.map((row, index) => (
                        <tr key={index}>{columns.map((column) => <td key={column} className="px-3 py-2 text-slate-700">{String(row[column] ?? "")}</td>)}</tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button type="button" onClick={commit} disabled={busy} className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60">
                  Intégrer au référentiel
                </button>
              </>
            ) : (
              <p className="mt-8 text-sm text-slate-500">L’aperçu apparaîtra ici après lecture du fichier.</p>
            )}
          </div>
        </section>

        <section className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <h2 className="font-semibold text-slate-950">Logs d’import</h2>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr><th className="px-4 py-3">Fichier</th><th className="px-4 py-3">Statut</th><th className="px-4 py-3">Lignes</th><th className="px-4 py-3">Durée</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{job.filename}</td>
                  <td className="px-4 py-3 text-slate-600">{job.status}</td>
                  <td className="px-4 py-3 text-slate-600">{job.imported_count}/{job.row_count}</td>
                  <td className="px-4 py-3 text-slate-600">{job.duration_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </>
  );
}
