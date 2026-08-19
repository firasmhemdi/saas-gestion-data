"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AuthCard } from "@/components/auth/auth-card";
import { Field } from "@/components/auth/field";
import { useAuth } from "@/components/auth/auth-provider";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const {
    login,
    verifyOtp,
    resendOtp,
    verifyEmail,
    resendEmailVerification,
    requestPasswordReset,
    confirmPasswordReset,
  } = useAuth();
  const [otpToken, setOtpToken] = useState<string | null>(null);
  const [verificationToken, setVerificationToken] = useState<string | null>(null);
  const [verificationEmail, setVerificationEmail] = useState<string | null>(null);
  const [resetStep, setResetStep] = useState<"request" | "confirm" | null>(null);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [resetEmail, setResetEmail] = useState<string | null>(null);
  const [deliveryHint, setDeliveryHint] = useState<string | null>(null);
  const [otpCode, setOtpCode] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleCredentials(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");

    setSubmitting(true);
    try {
      const result = await login(email, password);
      if ("requires_otp" in result) {
        setOtpToken(result.otp_token);
        setVerificationToken(null);
        setDeliveryHint(result.delivery_hint ?? "Un code de sécurité a été envoyé à votre adresse e-mail.");
        return;
      }
      if ("requires_email_verification" in result) {
        setVerificationToken(result.verification_token);
        setVerificationEmail(result.email);
        setOtpToken(null);
        setDeliveryHint(result.delivery_hint ?? "Un code de vérification a été envoyé à votre adresse e-mail.");
        return;
      }
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleOtp(event: React.FormEvent) {
    event.preventDefault();
    if (!otpToken) return;
    setError(null);
    setSubmitting(true);
    try {
      await verifyOtp(otpToken, otpCode);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResendOtp() {
    if (!otpToken) return;
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      const result = await resendOtp(otpToken);
      if ("requires_otp" in result) {
        setOtpToken(result.otp_token);
        setDeliveryHint(result.delivery_hint ?? "Un nouveau code de sécurité a été envoyé à votre adresse e-mail.");
        setNotice("Nouveau code envoyé.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de renvoyer le code.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEmailVerification(event: React.FormEvent) {
    event.preventDefault();
    if (!verificationToken) return;
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      await verifyEmail(verificationToken, emailCode);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResendEmailCode() {
    if (!verificationToken) return;
    setError(null);
    setNotice(null);
    setSubmitting(true);
    try {
      const result = await resendEmailVerification(verificationToken);
      if ("requires_email_verification" in result) {
        setVerificationToken(result.verification_token);
        setVerificationEmail(result.email);
        setDeliveryHint(result.delivery_hint ?? "Un nouveau code a été envoyé à votre adresse e-mail.");
        setNotice("Nouveau code envoyé.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de renvoyer le code.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePasswordResetRequest(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("reset_email") ?? "").trim();

    setSubmitting(true);
    try {
      const result = await requestPasswordReset(email);
      setResetEmail(result.email ?? email);
      setDeliveryHint(result.delivery_hint ?? "Si un compte existe, un code de réinitialisation a été envoyé.");
      if (result.reset_token) {
        setResetToken(result.reset_token);
        setResetStep("confirm");
        setNotice("Code envoyé. Vérifiez votre boîte e-mail.");
      } else {
        setNotice(result.delivery_hint ?? "Si un compte existe, un code de réinitialisation a été envoyé.");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'envoyer le code.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePasswordResetConfirm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!resetToken) return;
    setError(null);
    setNotice(null);

    if (newPassword.length < 8) {
      setError("Le nouveau mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await confirmPasswordReset(resetToken, resetCode, newPassword);
      setResetStep(null);
      setResetToken(null);
      setResetCode("");
      setNewPassword("");
      setConfirmNewPassword("");
      setDeliveryHint(null);
      setNotice(result.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de réinitialiser le mot de passe.");
    } finally {
      setSubmitting(false);
    }
  }

  if (resetStep === "request") {
    return (
      <AuthCard>
        <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Assistance connexion</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">Mot de passe oublié</h2>
        <p className="mt-1 text-sm text-slate-500">
          Saisissez votre e-mail. Nous enverrons un code pour définir un nouveau mot de passe.
        </p>

        <form onSubmit={handlePasswordResetRequest} className="mt-6 space-y-4">
          <Field
            label="Email du compte"
            id="reset_email"
            name="reset_email"
            type="email"
            autoComplete="email"
            required
            placeholder="vous@entreprise.fr"
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
            {submitting ? "Envoi…" : "Envoyer le code"}
          </button>

          <button
            type="button"
            onClick={() => {
              setResetStep(null);
              setError(null);
              setNotice(null);
              setDeliveryHint(null);
            }}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
          >
            Retour à la connexion
          </button>
        </form>
      </AuthCard>
    );
  }

  if (resetStep === "confirm") {
    return (
      <AuthCard>
        <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Sécurité du compte</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">Créer un nouveau mot de passe</h2>
        <p className="mt-1 text-sm text-slate-500">
          {deliveryHint ?? "Un code de réinitialisation a été envoyé à votre adresse e-mail."}
        </p>
        {resetEmail ? (
          <p className="mt-3 rounded-lg bg-teal-50 px-3 py-2 text-sm font-medium text-teal-800">
            Adresse : {resetEmail}
          </p>
        ) : null}

        <form onSubmit={handlePasswordResetConfirm} className="mt-6 space-y-4">
          <Field
            label="Code reçu par e-mail"
            id="reset_code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            placeholder="••••••"
            value={resetCode}
            onChange={(e) => setResetCode(e.target.value)}
          />
          <Field
            label="Nouveau mot de passe"
            id="new_password"
            type="password"
            autoComplete="new-password"
            required
            placeholder="••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <Field
            label="Confirmer le nouveau mot de passe"
            id="confirm_new_password"
            type="password"
            autoComplete="new-password"
            required
            placeholder="••••••••"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
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
            {submitting ? "Validation…" : "Réinitialiser le mot de passe"}
          </button>

          <button
            type="button"
            onClick={() => {
              setResetStep("request");
              setResetToken(null);
              setResetCode("");
              setNewPassword("");
              setConfirmNewPassword("");
              setError(null);
              setNotice(null);
            }}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
          >
            Renvoyer un code
          </button>
        </form>
      </AuthCard>
    );
  }

  if (verificationToken) {
    return (
      <AuthCard>
        <h2 className="text-xl font-semibold text-slate-900">Confirmation e-mail</h2>
        <p className="mt-1 text-sm text-slate-500">
          {deliveryHint ?? "Un code de vérification a été envoyé à votre adresse e-mail."}
        </p>
        {verificationEmail ? (
          <p className="mt-3 rounded-lg bg-teal-50 px-3 py-2 text-sm font-medium text-teal-800">
            Adresse : {verificationEmail}
          </p>
        ) : null}

        <form onSubmit={handleEmailVerification} className="mt-6 space-y-4">
          <Field
            label="Code reçu par e-mail"
            id="email_code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            placeholder="••••••"
            value={emailCode}
            onChange={(e) => setEmailCode(e.target.value)}
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
            onClick={handleResendEmailCode}
            disabled={submitting}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Renvoyer le code
          </button>
        </form>
      </AuthCard>
    );
  }

  if (otpToken) {
    return (
      <AuthCard>
        <h2 className="text-xl font-semibold text-slate-900">Vérification OTP</h2>
        <p className="mt-1 text-sm text-slate-500">
          {deliveryHint ?? "Un code de sécurité a été envoyé à votre adresse e-mail."}
        </p>

        <form onSubmit={handleOtp} className="mt-6 space-y-4">
          <Field
            label="Code à 6 chiffres"
            id="otp_code"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            placeholder="••••••"
            value={otpCode}
            onChange={(e) => setOtpCode(e.target.value)}
          />

          {error ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          ) : null}
          {notice ? (
            <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>
          ) : null}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Vérification…" : "Valider le code"}
          </button>

          <button
            type="button"
            onClick={handleResendOtp}
            disabled={submitting}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Renvoyer le code
          </button>

          <button
            type="button"
            onClick={() => {
              setOtpToken(null);
              setOtpCode("");
              setDeliveryHint(null);
            }}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
          >
            Retour à la connexion
          </button>
        </form>
      </AuthCard>
    );
  }

  return (
    <AuthCard>
      <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">Espace sécurisé</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">Connexion</h2>
      <p className="mt-1 text-sm text-slate-500">Accédez au cockpit ESG de votre entreprise.</p>

      <form onSubmit={handleCredentials} className="mt-6 space-y-4">
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
          autoComplete="current-password"
          required
          placeholder="••••••••"
        />

        {error ? (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        ) : null}
        {notice ? (
          <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{notice}</p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "Connexion…" : "Se connecter"}
        </button>
      </form>

      <div className="mt-3 text-right">
        <button
          type="button"
          onClick={() => {
            setResetStep("request");
            setError(null);
            setNotice(null);
          }}
          className="text-sm font-semibold text-teal-700 transition hover:text-teal-800 hover:underline"
        >
          Mot de passe oublié ?
        </button>
      </div>

      <p className="mt-6 text-center text-sm text-slate-500">
        Pas encore de compte ?{" "}
        <Link href="/register" className="font-semibold text-teal-700 hover:underline">
          Créer un compte
        </Link>
      </p>
    </AuthCard>
  );
}
