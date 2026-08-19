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
  const [mobileOpen, setMobileOpen] = useState(false);

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
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 shadow-[0_1px_18px_rgba(15,23,42,0.06)] backdrop-blur-xl">
      <div className="bg-[#07111f] text-white">
        <div className="mx-auto flex max-w-[1440px] flex-col gap-3 px-5 py-3 lg:px-6 xl:flex-row xl:items-center xl:px-8">
          <Link href="/dashboard" className="flex min-w-0 shrink-0 items-center gap-3 xl:w-[220px] 2xl:w-[250px]">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500 text-xs font-black text-slate-950 shadow-sm">
              SG
            </div>
            <div className="min-w-0">
              <p className="truncate text-[15px] font-bold leading-tight text-white">SaaS Gestion Data</p>
              <p className="truncate text-xs font-medium leading-tight text-slate-300">Pilotage environnemental et données ESG</p>
            </div>
          </Link>

          <nav className="hidden min-w-0 flex-1 items-center gap-1 xl:flex xl:justify-center xl:overflow-visible">
            {primaryLinks.map((link) => {
              const active = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`whitespace-nowrap rounded-xl border px-2.5 py-2 text-sm font-semibold transition 2xl:px-3.5 ${
                    active
                      ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-100"
                      : "border-transparent text-slate-300 hover:border-white/10 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex min-w-0 shrink-0 flex-wrap items-center gap-2 xl:justify-end">
            <SystemStatus />
            <CommandPalette />
            {user ? (
              <div className="hidden h-10 rounded-xl border border-white/10 bg-white/10 px-3 py-1.5 text-right shadow-sm ring-1 ring-white/5 sm:block">
                <p className="max-w-28 truncate text-sm font-semibold leading-4 text-white 2xl:max-w-40">{user.full_name}</p>
                <p className="text-xs leading-4 text-slate-300">{ROLE_LABELS[user.role]}</p>
              </div>
            ) : null}
            <button
              type="button"
              onClick={handleLogout}
              disabled={busy}
              className="h-10 rounded-xl border border-white/15 bg-white/10 px-3 text-sm font-semibold text-white transition hover:border-white/25 hover:bg-white/15 focus-visible:outline-emerald-300 disabled:opacity-60 2xl:px-4"
            >
              {busy ? "…" : "Déconnexion"}
            </button>
            <button
              type="button"
              onClick={() => setMobileOpen((value) => !value)}
              className="h-10 rounded-xl border border-white/15 bg-white/10 px-3.5 text-sm font-semibold text-white transition hover:border-white/25 hover:bg-white/15 xl:hidden"
              aria-expanded={mobileOpen}
            >
              Menu
            </button>
          </div>

          {mobileOpen ? (
            <nav className="grid w-full gap-1 rounded-xl border border-white/10 bg-white/5 p-1 xl:hidden">
              {primaryLinks.map((link) => {
                const active = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                      active
                        ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-100"
                        : "border-transparent text-slate-300 hover:border-white/10 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          ) : null}
        </div>
      </div>

      <div className="bg-white">
        <div className="mx-auto flex max-w-[1440px] items-center gap-2 px-5 py-2.5 lg:px-6 xl:px-8">
          <nav className="flex min-w-0 items-center gap-1 overflow-x-auto text-xs lg:flex-wrap lg:overflow-visible">
            <span className="mr-1 shrink-0 whitespace-nowrap text-[11px] font-bold uppercase tracking-wide text-slate-400">
              Modules
            </span>
            {secondaryLinks.map((link) => {
              const active = pathname === link.href || pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`whitespace-nowrap rounded-lg border px-2.5 py-1.5 font-semibold transition ${
                    active
                      ? "border-emerald-100 bg-emerald-50 text-emerald-800"
                      : "border-transparent text-slate-500 hover:border-slate-200 hover:bg-slate-50 hover:text-slate-900"
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
