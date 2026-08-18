"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { CommandPalette } from "@/components/command-palette";
import { useAuth } from "@/components/auth/auth-provider";
import { SystemStatus } from "@/components/system-status";
import { ROLE_LABELS } from "@/lib/roles";

export function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [busy, setBusy] = useState(false);

  async function handleLogout() {
    setBusy(true);
    await logout();
    router.replace("/login");
  }

  const isAdmin = user?.role === "admin";
  const isManager = isAdmin || user?.role === "responsable_environnement";
  const isWriter = isManager || user?.role === "consultant";

  const primaryLinks = [
    { href: "/dashboard", label: "Accueil" },
    ...(isManager ? [{ href: "/dashboard/analytics", label: "Analytics" }] : []),
    ...(isWriter ? [{ href: "/dashboard/quality", label: "Qualité" }] : []),
    { href: "/dashboard/assistant", label: "Assistant IA" },
    ...(isWriter ? [{ href: "/dashboard/documents", label: "Documents" }] : []),
  ];

  const secondaryLinks = [
    ...(isWriter ? [{ href: "/dashboard/entry", label: "Saisie" }] : []),
    ...(isWriter ? [{ href: "/dashboard/imports", label: "Imports" }] : []),
    ...(isWriter ? [{ href: "/dashboard/mapping", label: "Mapping" }] : []),
    ...(isManager ? [{ href: "/dashboard/sites", label: "Sites" }] : []),
    ...(isWriter ? [{ href: "/dashboard/data-sources", label: "Sources" }] : []),
    ...(isWriter ? [{ href: "/dashboard/reference", label: "Référentiel" }] : []),
    ...(isManager ? [{ href: "/dashboard/users", label: "Utilisateurs" }] : []),
    ...(isAdmin ? [{ href: "/dashboard/audit", label: "Audit" }] : []),
  ];

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 shadow-[0_1px_18px_rgba(15,23,42,0.05)] backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-700 text-xs font-bold text-white">
              SG
            </div>
            <div>
              <p className="whitespace-nowrap font-semibold leading-tight text-slate-900">SaaS Gestion Data</p>
              <p className="text-xs leading-tight text-slate-500">Cockpit ESG</p>
            </div>
          </div>

          <nav className="order-3 flex w-full items-center gap-1 overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-1 lg:order-2 lg:w-auto">
            {primaryLinks.map((link) => {
              const active = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition ${
                    active
                      ? "bg-white text-teal-700 shadow-sm"
                      : "text-slate-600 hover:bg-white/70 hover:text-slate-900"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="order-2 flex items-center gap-3 lg:order-3">
            <SystemStatus />
            <CommandPalette />
            {user ? (
              <div className="hidden rounded-lg bg-slate-50 px-3 py-2 text-right sm:block">
                <p className="text-sm font-semibold leading-tight text-slate-900">{user.full_name}</p>
                <p className="text-xs leading-tight text-slate-500">{ROLE_LABELS[user.role]}</p>
              </div>
            ) : null}
            <button
              type="button"
              onClick={handleLogout}
              disabled={busy}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-60"
            >
              {busy ? "…" : "Déconnexion"}
            </button>
          </div>
        </div>

        <nav className="mt-3 flex items-center gap-1 overflow-x-auto text-xs">
          {secondaryLinks.map((link) => {
            const active = pathname === link.href || pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`whitespace-nowrap rounded-lg px-3 py-1.5 font-semibold transition ${
                  active ? "bg-teal-50 text-teal-700" : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
