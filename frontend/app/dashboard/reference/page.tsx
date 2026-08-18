"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { api, ApiError } from "@/lib/api";
import { INDICATOR_CATEGORY_LABELS } from "@/lib/roles";
import type { Emission, EmissionPayload, Indicator, IndicatorCategory, IndicatorPayload } from "@/lib/types";

const isManager = (role: string | undefined) =>
  role === "admin" || role === "responsable_environnement";

const CATEGORIES: IndicatorCategory[] = ["energie", "eau", "dechets", "emissions", "matieres"];
const SCOPES = ["1", "2", "3"] as const;

function IndicatorForm({ onDone }: { onDone: () => Promise<void> }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [unit, setUnit] = useState("");
  const [category, setCategory] = useState<IndicatorCategory>("energie");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: IndicatorPayload = { code, name, unit, category, description: description || undefined };
      await api.post<Indicator>("/reference/indicators", payload);
      setCode("");
      setName("");
      setUnit("");
      setDescription("");
      await onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-3">
      <input required value={code} onChange={(e) => setCode(e.target.value)} placeholder="Code (ex. ELEC_CONS)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom de l'indicateur" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <input required value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="Unité (kWh, m³…)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <select value={category} onChange={(e) => setCategory(e.target.value as IndicatorCategory)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>
            {INDICATOR_CATEGORY_LABELS[c]}
          </option>
        ))}
      </select>
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optionnel)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <button type="submit" disabled={submitting} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60">
        {submitting ? "Création…" : "Ajouter l'indicateur"}
      </button>
      {error ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-3">{error}</p> : null}
    </form>
  );
}

function EmissionForm({ onDone }: { onDone: () => Promise<void> }) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [scope, setScope] = useState<"1" | "2" | "3">("2");
  const [factor, setFactor] = useState("");
  const [unit, setUnit] = useState("");
  const [year, setYear] = useState("2025");
  const [source, setSource] = useState("ADEME");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload: EmissionPayload = {
        code,
        name,
        scope,
        factor: Number(factor),
        unit,
        year: Number(year),
        source: source || undefined,
      };
      await api.post<Emission>("/reference/emissions", payload);
      setCode("");
      setName("");
      setFactor("");
      setUnit("");
      await onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-4">
      <input required value={code} onChange={(e) => setCode(e.target.value)} placeholder="Code (ex. FE_ELEC_FR)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom du facteur" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <select value={scope} onChange={(e) => setScope(e.target.value as "1" | "2" | "3")} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
        {SCOPES.map((s) => (
          <option key={s} value={s}>
            Scope {s}
          </option>
        ))}
      </select>
      <input required type="number" step="any" value={factor} onChange={(e) => setFactor(e.target.value)} placeholder="Facteur (0.052)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <input required value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="Unité (kgCO2e/kWh)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <input required type="number" value={year} onChange={(e) => setYear(e.target.value)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="Source (ADEME…)" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <button type="submit" disabled={submitting} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60">
        {submitting ? "Création…" : "Ajouter le facteur"}
      </button>
      {error ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-4">{error}</p> : null}
    </form>
  );
}

export default function ReferencePage() {
  const { user: currentUser } = useAuth();
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [emissions, setEmissions] = useState<Emission[]>([]);
  const [showIndicatorForm, setShowIndicatorForm] = useState(false);
  const [showEmissionForm, setShowEmissionForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [i, e] = await Promise.all([
        api.get<Indicator[]>("/reference/indicators"),
        api.get<Emission[]>("/reference/emissions"),
      ]);
      setIndicators(i);
      setEmissions(e);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger le référentiel.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const canManage = isManager(currentUser?.role);

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Référentiel des indicateurs</h1>
          <p className="mt-1 text-sm text-slate-500">
            Modèle de données du référentiel : indicateurs environnementaux et facteurs d&apos;émission carbone.
          </p>
        </div>

        {error ? (
          <p className="mt-6 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        ) : null}

        <section className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Indicateurs ({indicators.length})</h2>
            {canManage ? (
              <button
                type="button"
                onClick={() => setShowIndicatorForm((v) => !v)}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                {showIndicatorForm ? "Annuler" : "Ajouter un indicateur"}
              </button>
            ) : null}
          </div>

          {showIndicatorForm ? (
            <div className="mt-4">
              <IndicatorForm onDone={load} />
            </div>
          ) : null}

          {loading ? (
            <p className="mt-4 text-sm text-slate-500">Chargement…</p>
          ) : (
            <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Code</th>
                    <th className="px-4 py-3 font-semibold">Indicateur</th>
                    <th className="px-4 py-3 font-semibold">Unité</th>
                    <th className="px-4 py-3 font-semibold">Catégorie</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {indicators.map((ind) => (
                    <tr key={ind.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{ind.code}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{ind.name}</td>
                      <td className="px-4 py-3 text-slate-500">{ind.unit}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
                          {INDICATOR_CATEGORY_LABELS[ind.category]}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {indicators.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                        Aucun indicateur défini.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="mt-10">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Facteurs d&apos;émission ({emissions.length})</h2>
            {canManage ? (
              <button
                type="button"
                onClick={() => setShowEmissionForm((v) => !v)}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                {showEmissionForm ? "Annuler" : "Ajouter un facteur"}
              </button>
            ) : null}
          </div>

          {showEmissionForm ? (
            <div className="mt-4">
              <EmissionForm onDone={load} />
            </div>
          ) : null}

          {loading ? (
            <p className="mt-4 text-sm text-slate-500">Chargement…</p>
          ) : (
            <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Code</th>
                    <th className="px-4 py-3 font-semibold">Facteur</th>
                    <th className="px-4 py-3 font-semibold">Scope</th>
                    <th className="px-4 py-3 font-semibold">Valeur</th>
                    <th className="px-4 py-3 font-semibold">Année</th>
                    <th className="px-4 py-3 font-semibold">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {emissions.map((em) => (
                    <tr key={em.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{em.code}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{em.name}</td>
                      <td className="px-4 py-3 text-slate-500">Scope {em.scope}</td>
                      <td className="px-4 py-3 text-slate-700">
                        {em.factor} {em.unit}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{em.year}</td>
                      <td className="px-4 py-3 text-slate-500">{em.source ?? "—"}</td>
                    </tr>
                  ))}
                  {emissions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                        Aucun facteur d&apos;émission défini.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </>
  );
}
