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
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 shadow-[0_1px_20px_rgba(15,23,42,0.05)] backdrop-blur-xl">
      <div className="mx-auto max-w-[1560px] px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <Link href="/dashboard" className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white shadow-sm">
              SG
            </div>
            <div className="min-w-0">
              <p className="whitespace-nowrap text-base font-bold leading-tight text-slate-950">SaaS Gestion Data</p>
              <p className="truncate text-xs font-medium leading-tight text-slate-500">Pilotage environnemental</p>
            </div>
          </Link>

          <div className="flex shrink-0 items-center gap-2">
            <SystemStatus />
            <CommandPalette />
            {user ? (
              <div className="hidden rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-right sm:block">
                <p className="text-sm font-semibold leading-tight text-slate-900">{user.full_name}</p>
                <p className="text-xs leading-tight text-slate-500">{ROLE_LABELS[user.role]}</p>
              </div>
            ) : null}
            <button
              type="button"
              onClick={handleLogout}
              disabled={busy}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-60"
            >
              {busy ? "…" : "Déconnexion"}
            </button>
          </div>
        </div>

        <div className="mt-3 flex flex-col gap-2 border-t border-slate-100 pt-3 xl:flex-row xl:items-center xl:justify-between">
          <nav className="flex items-center gap-1 overflow-x-auto rounded-lg border border-slate-200 bg-slate-100 p-1">
            {primaryLinks.map((link) => {
              const active = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`whitespace-nowrap rounded-md px-3.5 py-2 text-sm font-semibold transition ${
                    active
                      ? "bg-white text-slate-950 shadow-sm ring-1 ring-slate-200"
                      : "text-slate-600 hover:bg-white/75 hover:text-slate-950"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <nav className="flex items-center gap-1 overflow-x-auto text-xs">
            {secondaryLinks.map((link) => {
              const active = pathname === link.href || pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`whitespace-nowrap rounded-lg px-3 py-1.5 font-semibold transition ${
                    active ? "bg-teal-50 text-teal-700 ring-1 ring-teal-100" : "text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
