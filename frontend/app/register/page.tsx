"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { Field } from "@/components/auth/field";
import { useAuth } from "@/components/auth/auth-provider";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const { register, verifyEmail, resendEmailVerification } = useAuth();
  const [verificationToken, setVerificationToken] = useState<string | null>(null);
  const [deliveryHint, setDeliveryHint] = useState<string | null>(null);
  const [verificationEmail, setVerificationEmail] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const form = new FormData(event.currentTarget);
    const fullName = String(form.get("full_name") ?? "").trim();
    const companyName = String(form.get("company_name") ?? "").trim();
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const confirmPassword = String(form.get("confirm_password") ?? "");

    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await register({
        email,
        full_name: fullName,
        password,
        company_name: companyName,
      });
      if ("requires_email_verification" in result) {
        setVerificationToken(result.verification_token);
        setVerificationEmail(result.email);
        setDeliveryHint(result.delivery_hint ?? "Un code de vérification a été envoyé à votre adresse e-mail.");
        setNotice("Compte créé. Vérifiez votre e-mail pour l'activer.");
        return;
      }
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyEmail(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!verificationToken) return;
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      await verifyEmail(verificationToken, code);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResendCode() {
    if (!verificationToken) return;
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      const result = await resendEmailVerification(verificationToken);
      if ("requires_email_verification" in result) {
        setVerificationToken(result.verification_token);
        setDeliveryHint(result.delivery_hint ?? "Un nouveau code a été envoyé à votre adresse e-mail.");
        setVerificationEmail(result.email);
        setNotice("Nouveau code envoyé.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de renvoyer le code.");
    } finally {
      setSubmitting(false);
    }
  }

  if (verificationToken) {
    return (
      <AuthCard>
        <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Confirmation e-mail</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">Activez votre compte</h2>
        <p className="mt-1 text-sm text-slate-500">
          {deliveryHint ?? "Un code de vérification a été envoyé à votre adresse e-mail."}
        </p>
        {verificationEmail ? (
          <p className="mt-2 rounded-lg bg-teal-50 px-3 py-2 text-sm font-medium text-teal-800">
            Adresse : {verificationEmail}
          </p>
        ) : null}

        <form onSubmit={handleVerifyEmail} className="mt-6 space-y-4">
          <Field
            label="Code reçu par e-mail"
            id="email_code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            placeholder="••••••"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />

          {notice ? (
            <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>
          ) : null}
          {error ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Validation…" : "Valider mon e-mail"}
          </button>

          <button
            type="button"
            onClick={handleResendCode}
            disabled={submitting}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Renvoyer le code
          </button>
        </form>
      </AuthCard>
    );
  }

  return (
    <AuthCard>
      <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Nouveau tenant</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">Créer votre compte</h2>
      <p className="mt-1 text-sm text-slate-500">
        Inscription : vous créez votre entreprise (tenant) et devenez administrateur.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <Field
          label="Nom complet"
          id="full_name"
          name="full_name"
          autoComplete="name"
          required
          placeholder="Marie Dupont"
        />
        <Field
          label="Entreprise"
          id="company_name"
          name="company_name"
          required
          placeholder="Nom de votre entreprise"
        />
        <Field
          label="Email professionnel"
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          placeholder="vous@entreprise.fr"
        />
        <Field
          label="Mot de passe"
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          placeholder="8 caractères minimum"
        />
        <Field
          label="Confirmer le mot de passe"
          id="confirm_password"
          name="confirm_password"
          type="password"
          autoComplete="new-password"
          required
          placeholder="••••••••"
        />

        {error ? (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Création…" : "Créer mon compte"}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Déjà un compte ?{" "}
        <Link href="/login" className="font-semibold text-teal-700 hover:underline">
          Se connecter
        </Link>
      </p>
    </AuthCard>
  );
}
