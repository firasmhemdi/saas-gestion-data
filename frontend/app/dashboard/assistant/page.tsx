"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { api, ApiError } from "@/lib/api";
import type { AssistantAnswer } from "@/lib/types";

const examples = [
  "Quel site possède la consommation la plus élevée ?",
  "Résume les principaux volumes environnementaux.",
  "Quelles sources appuient la dernière réponse ?",
];

const promptGroups = [
  ["Comparaison", "Quel site a les émissions carbone les plus élevées ?"],
  ["Qualité", "Quelles données doivent être vérifiées en priorité ?"],
  ["Reporting", "Prépare une synthèse ESG courte pour la direction."],
];

export default function AssistantPage() {
  const [question, setQuestion] = useState(examples[0]);
  const [history, setHistory] = useState<AssistantAnswer[]>([]);
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);

  const loadHistory = useCallback(async () => {
    try {
      setHistory(await api.get<AssistantAnswer[]>("/assistant/history"));
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.post<AssistantAnswer>("/assistant/query", { question });
      setAnswer(result);
      setCopied(false);
      setQuestion("");
      await loadHistory();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'interroger l'assistant.");
    } finally {
      setBusy(false);
    }
  }

  async function copyAnswer() {
    if (!answer) return;
    await navigator.clipboard.writeText(answer.answer);
    setCopied(true);
  }

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Sprint 8</p>
          <h1 className="text-2xl font-bold text-slate-950">Assistant IA sourcé</h1>
          <p className="mt-1 text-sm text-slate-500">
            Posez une question métier; l&apos;assistant répond avec les données disponibles et cite les sources utilisées.
          </p>
        </div>

        <section className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-5 grid gap-3 sm:grid-cols-3">
              {promptGroups.map(([label, prompt]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => setQuestion(prompt)}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-left transition hover:border-teal-200 hover:bg-teal-50"
                >
                  <span className="block text-xs font-semibold uppercase tracking-wide text-teal-700">{label}</span>
                  <span className="mt-1 block text-sm font-medium leading-5 text-slate-700">{prompt}</span>
                </button>
              ))}
            </div>
            <form onSubmit={ask}>
              <label className="text-sm font-semibold text-slate-900" htmlFor="question">Question</label>
              <textarea
                id="question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={4}
                className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
                placeholder="Ex. Quel site consomme le plus d'électricité ?"
              />
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-2">
                  {examples.map((example) => (
                    <button key={example} type="button" onClick={() => setQuestion(example)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">
                      {example}
                    </button>
                  ))}
                </div>
                <button disabled={busy || question.trim().length < 3} className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50">
                  {busy ? "Analyse…" : "Interroger"}
                </button>
              </div>
            </form>
            {error ? <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

            <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Réponse</p>
                <button
                  type="button"
                  onClick={copyAnswer}
                  disabled={!answer}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                >
                  {copied ? "Copiée" : "Copier"}
                </button>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-700">
                {answer?.answer ?? "Lancez une question pour obtenir une réponse contextualisée."}
              </p>
              {answer?.sources.length ? (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Sources utilisées ({answer.sources.length})
                  </p>
                  <div className="mt-2 grid gap-2">
                    {answer.sources.map((source, index) => (
                      <div key={`${source.data_id}-${index}`} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">
                        <span className="font-semibold text-slate-900">{source.site ?? "Source"}</span>
                        {" · "}
                        {source.indicator ?? "Indicateur"}
                        {" · "}
                        {source.period ?? "période non renseignée"}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-semibold text-slate-950">Historique des requêtes</h2>
            <div className="mt-4 space-y-3">
              {history.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setAnswer(item)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-3 text-left transition hover:border-teal-200 hover:bg-teal-50"
                >
                  <p className="line-clamp-2 text-sm font-medium text-slate-900">{item.question}</p>
                  <p className="mt-1 text-xs text-slate-500">{new Date(item.created_at).toLocaleString("fr-FR")}</p>
                </button>
              ))}
              {history.length === 0 ? (
                <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-8 text-center text-sm text-slate-500">
                  Aucune requête enregistrée.
                </p>
              ) : null}
            </div>
          </aside>
        </section>
      </main>
    </>
  );
}
