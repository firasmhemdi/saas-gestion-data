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
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white shadow-[0_1px_18px_rgba(15,23,42,0.08)]">
      <div className="bg-[#07111f] text-white">
        <div className="mx-auto flex max-w-[1560px] items-center justify-between gap-4 px-4 py-3">
          <Link href="/dashboard" className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500 text-xs font-black text-slate-950 shadow-sm">
              SG
            </div>
            <div className="min-w-0">
              <p className="whitespace-nowrap text-base font-bold leading-tight">SaaS Gestion Data</p>
              <p className="truncate text-xs font-medium leading-tight text-slate-300">Pilotage environnemental et données ESG</p>
            </div>
          </Link>

          <div className="flex shrink-0 items-center gap-2">
            <SystemStatus />
            <CommandPalette />
            {user ? (
              <div className="hidden rounded-lg border border-white/10 bg-white/10 px-3 py-2 text-right sm:block">
                <p className="text-sm font-semibold leading-tight text-white">{user.full_name}</p>
                <p className="text-xs leading-tight text-slate-300">{ROLE_LABELS[user.role]}</p>
              </div>
            ) : null}
            <button
              type="button"
              onClick={handleLogout}
              disabled={busy}
              className="rounded-lg border border-white/15 bg-white/10 px-3 py-2 text-sm font-semibold text-white transition hover:bg-white/15 disabled:opacity-60"
            >
              {busy ? "…" : "Déconnexion"}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white">
        <div className="mx-auto flex max-w-[1560px] flex-col gap-2 px-4 py-2 xl:flex-row xl:items-center xl:justify-between">
          <nav className="flex items-center gap-1 overflow-x-auto">
            {primaryLinks.map((link) => {
              const active = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-semibold transition ${
                    active
                      ? "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-100"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
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
                  className={`whitespace-nowrap rounded-md px-2.5 py-1.5 font-semibold transition ${
                    active ? "bg-slate-950 text-white" : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
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
