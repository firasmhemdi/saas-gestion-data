"use client";

import { useEffect, useState } from "react";

import { API_URL } from "@/lib/api";

export function SystemStatus() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    const healthUrl = API_URL.replace(/\/api\/v1$/, "/health");

    async function check() {
      try {
        const response = await fetch(healthUrl, { cache: "no-store" });
        if (!cancelled) setOnline(response.ok);
      } catch {
        if (!cancelled) setOnline(false);
      }
    }

    check();
    const timer = window.setInterval(check, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const label = online === null ? "Vérification" : online ? "API active" : "API indisponible";
  const dot = online === null ? "bg-amber-400" : online ? "bg-emerald-500" : "bg-rose-500";

  return (
    <div className="hidden h-11 items-center gap-2 rounded-xl border border-white/10 bg-white px-3.5 text-xs font-semibold text-slate-700 shadow-sm transition xl:flex">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </div>
  );
}
