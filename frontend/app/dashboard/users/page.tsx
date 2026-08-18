"use client";

import { useCallback, useEffect, useState } from "react";

import { Navbar } from "@/components/auth/navbar";
import { useAuth } from "@/components/auth/auth-provider";
import { RoleBadge } from "@/components/users/role-badge";
import { api, ApiError } from "@/lib/api";
import { ROLE_LABELS, ROLE_OPTIONS } from "@/lib/roles";
import type { Role, User, UserCreatePayload } from "@/lib/types";

function CreateUserForm({ onCreated }: { onCreated: () => Promise<void> }) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("lecture_seule");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    setSubmitting(true);
    try {
      const payload: UserCreatePayload = { email, full_name: fullName, password, role };
      await api.post<User>("/users", payload);
      setEmail("");
      setFullName("");
      setPassword("");
      setRole("lecture_seule");
      setOpen(false);
      await onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
      >
        {open ? "Annuler" : "Ajouter un utilisateur"}
      </button>

      {open ? (
        <form
          onSubmit={handleSubmit}
          className="mt-4 grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-2"
        >
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Email professionnel
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="collaborateur@entreprise.fr"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Nom complet</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Jean Martin"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              Mot de passe provisoire
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="8 caractères minimum"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Rôle</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </div>

          {error ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">
              {error}
            </p>
          ) : null}

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-60"
            >
              {submitting ? "Création…" : "Créer l'utilisateur"}
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}

function RoleEditor({
  user,
  onChanged,
}: {
  user: User;
  onChanged: () => Promise<void>;
}) {
  const { user: currentUser } = useAuth();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function changeRole(role: Role) {
    if (role === user.role) return;
    setSaving(true);
    setError(null);
    try {
      await api.patch<User>(`/users/${user.id}`, { role });
      await onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de modifier le rôle.");
    } finally {
      setSaving(false);
    }
  }

  if (user.id === currentUser?.id) {
    return (
      <span className="text-xs text-slate-400" title="Vous ne pouvez pas modifier votre propre rôle">
        Vous
      </span>
    );
  }

  return (
    <div>
      <select
        value={user.role}
        onChange={(e) => changeRole(e.target.value as Role)}
        disabled={saving}
        className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm disabled:opacity-60"
      >
        {ROLE_OPTIONS.map((r) => (
          <option key={r} value={r}>
            {ROLE_LABELS[r]}
          </option>
        ))}
      </select>
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
    </div>
  );
}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setUsers(await api.get<User[]>("/users"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les utilisateurs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const isAdmin = currentUser?.role === "admin";

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Gestion des utilisateurs</h1>
            <p className="mt-1 text-sm text-slate-500">
              Les utilisateurs et rôles sont isolés par entreprise (tenant).
            </p>
          </div>
          {isAdmin ? <CreateUserForm onCreated={load} /> : null}
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
                  <th className="px-4 py-3 font-semibold">Utilisateur</th>
                  <th className="px-4 py-3 font-semibold">Rôle</th>
                  <th className="px-4 py-3 font-semibold">Statut</th>
                  {isAdmin ? <th className="px-4 py-3 font-semibold">Modifier le rôle</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-900">{u.full_name}</p>
                      <p className="text-xs text-slate-500">{u.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      <RoleBadge role={u.role} />
                    </td>
                    <td className="px-4 py-3">
                      {u.is_active ? (
                        <span className="text-xs font-medium text-emerald-600">Actif</span>
                      ) : (
                        <span className="text-xs font-medium text-slate-400">Inactif</span>
                      )}
                    </td>
                    {isAdmin ? (
                      <td className="px-4 py-3">
                        <RoleEditor user={u} onChanged={load} />
                      </td>
                    ) : null}
                  </tr>
                ))}
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                      Aucun utilisateur.
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
