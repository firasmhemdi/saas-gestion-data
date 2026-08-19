"use client";

import Link from "next/link";
import { useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { DemoTour } from "@/components/demo-tour";
import { api, ApiError } from "@/lib/api";
import { ROLE_LABELS } from "@/lib/roles";
import type { User } from "@/lib/types";

const quickActions = [
  ["Dashboard ESG", "/dashboard/analytics", "Visualiser les KPI et les scopes carbone."],
  ["Contrôle qualité", "/dashboard/quality", "Corriger les alertes avant validation."],
  ["Assistant IA", "/dashboard/assistant", "Interroger les données avec sources."],
  ["Documents", "/dashboard/documents", "Extraire et valider les factures/bordereaux."],
];

const businessModules = [
  ["Collecte", "Données", "Imports, saisie et journal des traitements", "/dashboard/imports", "Opérationnel"],
  ["Intégration", "Mapping", "Connecteurs, règles et synchronisations", "/dashboard/mapping", "Opérationnel"],
  ["Documents", "OCR", "Photos, classification et validation humaine", "/dashboard/documents", "Automatisé"],
  ["Qualité", "Contrôle", "Alertes, normalisation et workflow de validation", "/dashboard/quality", "Automatisé"],
  ["Analytics", "ESG", "Indicateurs, émissions et comparaisons multi-sites", "/dashboard/analytics", "Pilotage"],
  ["Assistant", "IA", "Questions métier, citations et historique", "/dashboard/assistant", "Sourcé"],
];

function OtpToggle() {
  const { user, logout } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!user) return null;
  const current = user;

  async function toggle() {
    setError(null);
    setBusy(true);
    try {
      await api.patch<User>("/auth/otp/settings", {
        enabled: !current.otp_enabled,
        password,
      });
      setPassword("");
      await logout();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de modifier la sécurité.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-surface rounded-lg p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-slate-950">Sécurité</h2>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            {user.otp_enabled
              ? "La double authentification est active sur ce compte."
              : "Activez l'OTP pour renforcer la protection des comptes sensibles."}
          </p>
        </div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${user.otp_enabled ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
          {user.otp_enabled ? "Protégé" : "À activer"}
        </span>
      </div>

      {!user.otp_enabled ? (
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Confirmez votre mot de passe"
          className="mt-4 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm shadow-sm"
        />
      ) : null}

      {error ? <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

      <button
        type="button"
        onClick={toggle}
        disabled={busy || (!user.otp_enabled && !password)}
        className={`mt-4 rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${
          user.otp_enabled ? "bg-rose-600 hover:bg-rose-700" : "bg-teal-700 hover:bg-teal-800"
        }`}
      >
        {busy ? "…" : user.otp_enabled ? "Désactiver l'OTP" : "Activer l'OTP"}
      </button>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null;

  const createdAt = new Date(user.created_at).toLocaleDateString("fr-FR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8">
        <section className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="app-surface rounded-lg p-6">
            <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Cockpit de pilotage environnemental</p>
            <h1 className="mt-3 max-w-3xl text-3xl font-bold leading-tight text-slate-950 md:text-4xl">
              Bonjour {user.full_name.split(" ")[0]}, votre plateforme couvre maintenant toute la chaîne ESG.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
              De la collecte brute jusqu&apos;au dashboard et à l&apos;assistant IA, chaque module apporte une valeur métier claire pour piloter les données environnementales.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ["Périmètre", "Complet", "Collecte, qualité, reporting"],
                ["Fiabilité", "Workflow", "Alertes, normalisation, validation"],
                ["Pilotage", "ESG + IA", "KPI, scopes et réponses sourcées"],
              ].map(([label, value, detail]) => (
                <div key={label} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
                  <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg bg-slate-950 p-5 text-white shadow-xl">
            <p className="text-xs uppercase tracking-wide text-teal-200">Session</p>
            <div className="mt-4 space-y-3">
              <div className="rounded-lg bg-white/10 p-4">
                <p className="text-xs text-slate-300">Utilisateur</p>
                <p className="mt-1 font-semibold">{user.full_name}</p>
                <p className="text-xs text-slate-300">{user.email}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-white/10 p-4">
                  <p className="text-xs text-slate-300">Rôle</p>
                  <p className="mt-1 text-sm font-semibold">{ROLE_LABELS[user.role]}</p>
                </div>
                <div className="rounded-lg bg-white/10 p-4">
                  <p className="text-xs text-slate-300">Tenant</p>
                  <p className="mt-1 text-sm font-semibold">#{user.company_id}</p>
                </div>
              </div>
              <div className="rounded-lg bg-teal-400/15 p-4">
                <p className="text-xs text-teal-100">Membre depuis</p>
                <p className="mt-1 text-sm font-semibold">{createdAt}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {quickActions.map(([title, href, description]) => (
            <Link key={href} href={href} className="group app-surface rounded-lg p-5 transition hover:-translate-y-0.5 hover:border-teal-200 hover:shadow-lg">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-sm font-bold text-teal-700">
                {title.slice(0, 2)}
              </div>
              <h2 className="mt-4 font-semibold text-slate-950">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
              <p className="mt-4 text-sm font-semibold text-teal-700 group-hover:text-teal-800">Ouvrir</p>
            </Link>
          ))}
        </section>

        <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_0.7fr]">
          <div className="grid gap-4">
            <DemoTour />
            <div className="app-surface rounded-lg p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-950">Modules métier</h2>
                <p className="mt-1 text-sm text-slate-500">Vue synthétique des capacités clés de la plateforme.</p>
              </div>
              <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">Production ready</span>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {businessModules.map(([area, title, description, href, status]) => (
                <Link key={area} href={href} className="rounded-lg border border-slate-200 bg-white p-4 transition hover:border-teal-200 hover:bg-teal-50/40">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{area}</p>
                      <h3 className="mt-1 font-semibold text-slate-950">{title}</h3>
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${status === "Opérationnel" ? "bg-emerald-50 text-emerald-700" : "bg-teal-50 text-teal-700"}`}>
                      {status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-500">{description}</p>
                </Link>
              ))}
            </div>
          </div>
          </div>

          <div className="grid gap-4">
            <OtpToggle />
            <div className="app-surface rounded-lg p-5">
              <h2 className="font-semibold text-slate-950">Parcours recommandé</h2>
              <div className="mt-4 space-y-3">
                {["Créer/importer une donnée", "Contrôler la qualité", "Afficher le dashboard ESG", "Poser une question à l'assistant IA"].map((step, index) => (
                  <div key={step} className="flex gap-3 rounded-lg bg-slate-50 p-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-950 text-xs font-semibold text-white">
                      {index + 1}
                    </span>
                    <p className="text-sm font-medium text-slate-700">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
