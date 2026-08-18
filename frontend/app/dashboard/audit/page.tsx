"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { api, ApiError } from "@/lib/api";
import { AUDIT_ACTION_LABELS } from "@/lib/roles";
import type { AuditLog } from "@/lib/types";

const ACTION_STYLES: Record<string, string> = {
  register: "bg-emerald-50 text-emerald-700",
  login: "bg-sky-50 text-sky-700",
  login_failed: "bg-red-50 text-red-700",
  logout: "bg-slate-100 text-slate-600",
  refresh: "bg-violet-50 text-violet-700",
  password_change: "bg-amber-50 text-amber-700",
  user_role_change: "bg-indigo-50 text-indigo-700",
};

function formatDetails(details: Record<string, unknown> | null): string {
  if (!details) return "—";
  const parts = Object.entries(details)
    .filter(([, value]) => value !== null)
    .map(([key, value]) => `${key}: ${value}`);
  return parts.length ? parts.join(" · ") : "—";
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setLogs(await api.get<AuditLog[]>("/users/audit/logs"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger le journal d'audit.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Journal d&apos;audit</h1>
          <p className="mt-1 text-sm text-slate-500">
            Traçabilité des actions sensibles de votre entreprise (50 dernières entrées).
          </p>
        </div>

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
                  <th className="px-4 py-3 font-semibold">Action</th>
                  <th className="px-4 py-3 font-semibold">Adresse IP</th>
                  <th className="px-4 py-3 font-semibold">Détails</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-500">
                      {new Date(log.created_at).toLocaleString("fr-FR", {
                        dateStyle: "short",
                        timeStyle: "medium",
                      })}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                          ACTION_STYLES[log.action] ?? "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {AUDIT_ACTION_LABELS[log.action] ?? log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{log.ip_address ?? "—"}</td>
                    <td className="max-w-xs truncate px-4 py-3 text-xs text-slate-500">
                      {formatDetails(log.details)}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                      Aucune entrée d&apos;audit pour le moment.
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
