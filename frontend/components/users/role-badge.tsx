import type { Role } from "@/lib/types";
import { ROLE_LABELS } from "@/lib/roles";

const BADGE_STYLES: Record<Role, string> = {
  admin: "bg-emerald-50 text-emerald-700",
  responsable_environnement: "bg-sky-50 text-sky-700",
  consultant: "bg-violet-50 text-violet-700",
  lecture_seule: "bg-slate-100 text-slate-600",
};

export function RoleBadge({ role }: { role: Role }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE_STYLES[role]}`}
    >
      {ROLE_LABELS[role]}
    </span>
  );
}
