"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { api, ApiError } from "@/lib/api";
import { SOURCE_TYPE_LABELS } from "@/lib/roles";
import type { DataSource, DataSourcePayload, Site, SourceType } from "@/lib/types";

const isManager = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement";

const SOURCE_TYPES: SourceType[] = ["excel", "api", "sql", "erp", "iot"];

function parseConfig(raw: string): Record<string, unknown> {
  if (!raw.trim()) return {};
  const parsed = JSON.parse(raw);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("La configuration doit être un objet JSON.");
  }
  return parsed as Record<string, unknown>;
}

function DataSourceForm({
  sites,
  onDone,
  source,
}: {
  sites: Site[];
  onDone: () => Promise<void>;
  source?: DataSource;
}) {
  const [name, setName] = useState(source?.name ?? "");
  const [sourceType, setSourceType] = useState<SourceType>(source?.source_type ?? "excel");
  const [siteId, setSiteId] = useState<string>(source?.site_id ? String(source.site_id) : "");
  const [config, setConfig] = useState(
    source ? JSON.stringify(source.config ?? {}, null, 2) : "{\n  \n}",
  );
  const [isActive, setIsActive] = useState(source?.is_active ?? true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: DataSourcePayload = {
        name,
        source_type: sourceType,
        site_id: siteId ? Number(siteId) : null,
        config: parseConfig(config),
        is_active: isActive,
      };
      if (source) await api.patch<DataSource>(`/data-sources/${source.id}`, payload);
      else await api.post<DataSource>("/data-sources", payload);
      setName("");
      setConfig("{\n  \n}");
      setSiteId("");
      setSourceType("excel");
      await onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-2">
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Nom de la source</label>
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Compteur API EDF"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Type</label>
        <select
          value={sourceType}
          onChange={(e) => setSourceType(e.target.value as SourceType)}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
        >
          {SOURCE_TYPES.map((t) => (
            <option key={t} value={t}>
              {SOURCE_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Site associé (optionnel)</label>
        <select
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
        >
          <option value="">Aucun site</option>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex items-end pb-1">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-emerald-600"
          />
          Source active
        </label>
      </div>
      <div className="sm:col-span-2">
        <label className="mb-1.5 block text-sm font-medium text-slate-700">
          Configuration (JSON, identifiants chiffrés AES-256 au repos)
        </label>
        <textarea
          value={config}
          onChange={(e) => setConfig(e.target.value)}
          rows={5}
          spellCheck={false}
          placeholder='{&#10;  "base_url": "https://api.edf.fr",&#10;  "api_key": "secret"&#10;}'
          className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs"
        />
      </div>

      {error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">{error}</p>
      ) : null}

      <div className="sm:col-span-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60"
        >
          {submitting ? "Enregistrement…" : source ? "Enregistrer les modifications" : "Créer la source"}
        </button>
      </div>
    </form>
  );
}

export default function DataSourcesPage() {
  const { user: currentUser } = useAuth();
  const [sources, setSources] = useState<DataSource[]>([]);
  const [sites, setSites] = useState<Site[]>([]);
  const [editing, setEditing] = useState<DataSource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, sitesData] = await Promise.all([
        api.get<DataSource[]>("/data-sources"),
        api.get<Site[]>("/sites"),
      ]);
      setSources(s);
      setSites(sitesData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les sources de données.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const canManage = isManager(currentUser?.role);

  async function removeSource(source: DataSource) {
    if (!window.confirm(`Supprimer la source « ${source.name} » ?`)) return;
    try {
      await api.delete<void>(`/data-sources/${source.id}`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de supprimer la source.");
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Sources de données</h1>
            <p className="mt-1 text-sm text-slate-500">
              Préparez la collecte (fichiers, API, SQL, ERP, IoT). Les identifiants sont chiffrés en base.
            </p>
          </div>
          {canManage ? (
            <button
              type="button"
              onClick={() => setEditing(editing ? null : { id: 0, company_id: 0, site_id: null, name: "", source_type: "excel", config: {}, is_active: true, created_at: "", updated_at: "" })}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
              {editing ? "Annuler" : "Ajouter une source"}
            </button>
          ) : null}
        </div>

        {editing ? (
          <div className="mt-6">
            <DataSourceForm sites={sites} source={editing} onDone={load} />
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
                  <th className="px-4 py-3 font-semibold">Source</th>
                  <th className="px-4 py-3 font-semibold">Type</th>
                  <th className="px-4 py-3 font-semibold">Statut</th>
                  {canManage ? <th className="px-4 py-3 font-semibold">Actions</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sources.map((source) => (
                  <tr key={source.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{source.name}</p>
                      <p className="font-mono text-xs text-slate-400">
                        {sites.find((s) => s.id === source.site_id)?.name ?? "Sans site"}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-semibold text-sky-700">
                        {SOURCE_TYPE_LABELS[source.source_type]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {source.is_active ? (
                        <span className="text-xs font-medium text-emerald-600">Active</span>
                      ) : (
                        <span className="text-xs font-medium text-slate-400">Inactive</span>
                      )}
                    </td>
                    {canManage ? (
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => setEditing(editing?.id === source.id ? null : source)}
                            className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                          >
                            Modifier
                          </button>
                          <button
                            type="button"
                            onClick={() => removeSource(source)}
                            className="rounded-lg border border-red-200 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                          >
                            Supprimer
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
                {sources.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                      Aucune source de données pour le moment.
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
