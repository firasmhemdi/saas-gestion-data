"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { api, ApiError } from "@/lib/api";
import type { Site, SitePayload } from "@/lib/types";

const isManager = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement";

function SiteForm({
  onDone,
  site,
}: {
  onDone: () => Promise<void>;
  site?: Site;
}) {
  const [name, setName] = useState(site?.name ?? "");
  const [code, setCode] = useState(site?.code ?? "");
  const [location, setLocation] = useState(site?.location ?? "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: SitePayload = { name, code: code || undefined, location: location || undefined };
      if (site) await api.patch<Site>(`/sites/${site.id}`, payload);
      else await api.post<Site>("/sites", payload);
      setName("");
      setCode("");
      setLocation("");
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
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Nom du site</label>
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Usine de Lyon"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Code</label>
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="LYN-01"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      </div>
      <div className="sm:col-span-2">
        <label className="mb-1.5 block text-sm font-medium text-slate-700">Localisation</label>
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Lyon, France"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
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
          {submitting ? "Enregistrement…" : site ? "Enregistrer les modifications" : "Ajouter le site"}
        </button>
      </div>
    </form>
  );
}

export default function SitesPage() {
  const { user: currentUser } = useAuth();
  const [sites, setSites] = useState<Site[]>([]);
  const [editing, setEditing] = useState<Site | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSites(await api.get<Site[]>("/sites"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les sites.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const canManage = isManager(currentUser?.role);

  async function removeSite(site: Site) {
    if (!window.confirm(`Supprimer le site « ${site.name} » ?`)) return;
    try {
      await api.delete<void>(`/sites/${site.id}`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de supprimer le site.");
    }
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Sites industriels</h1>
            <p className="mt-1 text-sm text-slate-500">
              Structurez vos données environnementales par site. Les sites sont isolés par entreprise (tenant).
            </p>
          </div>
          {canManage ? (
            <button
              type="button"
              onClick={() => setEditing(editing ? null : { id: 0, company_id: 0, name: "", code: "", location: "", created_at: "" })}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
              {editing ? "Annuler" : "Ajouter un site"}
            </button>
          ) : null}
        </div>

        {editing ? (
          <div className="mt-6">
            <SiteForm onDone={load} />
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
                  <th className="px-4 py-3 font-semibold">Nom</th>
                  <th className="px-4 py-3 font-semibold">Code</th>
                  <th className="px-4 py-3 font-semibold">Localisation</th>
                  {canManage ? <th className="px-4 py-3 font-semibold">Actions</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sites.map((site) => (
                  <tr key={site.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{site.name}</td>
                    <td className="px-4 py-3 text-slate-500">{site.code ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-500">{site.location ?? "—"}</td>
                    {canManage ? (
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => setEditing(editing?.id === site.id ? null : site)}
                            className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                          >
                            Modifier
                          </button>
                          <button
                            type="button"
                            onClick={() => removeSite(site)}
                            className="rounded-lg border border-red-200 px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                          >
                            Supprimer
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
                {sites.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                      Aucun site pour le moment.
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
