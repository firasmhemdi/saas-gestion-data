import base64
import json
import logging
import smtplib
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.models.user import User


class EmailDeliveryError(Exception):
    pass


logger = logging.getLogger(__name__)


def _sender_header(name: str, email: str) -> str:
    return f"{name} <{email}>"


def _safe_resend_error_message(error_body: str) -> str:
    body = error_body.lower()
    if "domain" in body or "verify" in body or "own email address" in body:
        return (
            "Resend a refusé l'envoi. Vérifiez que RESEND_FROM_EMAIL utilise un domaine vérifié, "
            "ou testez avec l'adresse e-mail autorisée par votre compte Resend."
        )
    if "api key" in body or "unauthorized" in body or "forbidden" in body:
        return "Resend a refusé l'envoi. Vérifiez la variable RESEND_API_KEY sur Render."
    return "Impossible d'envoyer l'e-mail OTP."


def _safe_mailjet_error_message(error_body: str) -> str:
    body = error_body.lower()
    if "sender" in body or "from" in body or "prevalidated" in body or "allowed" in body:
        return (
            "Mailjet a refusé l'envoi. Vérifiez que MAILJET_FROM_EMAIL est une adresse expéditeur "
            "validée dans Mailjet > Senders & Domains."
        )
    if "api key" in body or "unauthorized" in body or "forbidden" in body or "authentication" in body:
        return "Mailjet a refusé l'envoi. Vérifiez MAILJET_API_KEY et MAILJET_SECRET_KEY sur Render."
    return "Impossible d'envoyer l'e-mail OTP avec Mailjet."


def _send_with_resend(user: User, *, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        raise EmailDeliveryError("Service e-mail API non configuré.")

    from_email = settings.resend_from_email or "onboarding@resend.dev"
    payload = {
        "from": _sender_header(settings.smtp_from_name, from_email),
        "to": [user.email],
        "subject": subject,
        "text": text,
        "html": html,
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "saas-gestion-data/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            if response.status >= 400:
                raise EmailDeliveryError("Impossible d'envoyer l'e-mail OTP.")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        logger.warning("Resend rejected email delivery: status=%s body=%s", exc.code, error_body)
        raise EmailDeliveryError(_safe_resend_error_message(error_body)) from exc
    except URLError as exc:
        logger.warning("Resend email delivery unavailable: %s", exc)
        raise EmailDeliveryError("Impossible de contacter le service e-mail Resend.") from exc


def _send_with_mailjet(user: User, *, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    if not settings.mailjet_api_key or not settings.mailjet_secret_key:
        raise EmailDeliveryError("Service e-mail Mailjet non configuré.")
    if not settings.mailjet_from_email:
        raise EmailDeliveryError("MAILJET_FROM_EMAIL doit contenir une adresse expéditeur validée dans Mailjet.")

    sender_name = settings.mailjet_from_name or settings.smtp_from_name
    payload = {
        "Messages": [
            {
                "From": {"Email": settings.mailjet_from_email, "Name": sender_name},
                "To": [{"Email": user.email, "Name": user.full_name}],
                "Subject": subject,
                "TextPart": text,
                "HTMLPart": html,
            }
        ]
    }
    credentials = f"{settings.mailjet_api_key}:{settings.mailjet_secret_key}".encode("utf-8")
    request = Request(
        "https://api.mailjet.com/v3.1/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Basic {base64.b64encode(credentials).decode('ascii')}",
            "Content-Type": "application/json",
            "User-Agent": "saas-gestion-data/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            if response.status >= 400:
                raise EmailDeliveryError("Impossible d'envoyer l'e-mail OTP avec Mailjet.")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        logger.warning("Mailjet rejected email delivery: status=%s body=%s", exc.code, error_body)
        raise EmailDeliveryError(_safe_mailjet_error_message(error_body)) from exc
    except URLError as exc:
        logger.warning("Mailjet email delivery unavailable: %s", exc)
        raise EmailDeliveryError("Impossible de contacter le service e-mail Mailjet.") from exc


def _send_with_smtp(user: User, *, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        raise EmailDeliveryError("Service e-mail OTP non configuré.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _sender_header(settings.smtp_from_name, settings.smtp_from_email)
    message["To"] = user.email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception as exc:
        raise EmailDeliveryError("Impossible d'envoyer l'e-mail OTP.") from exc


def _send_code_email(user: User, *, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    provider = settings.email_provider.lower()
    if provider == "resend":
        _send_with_resend(user, subject=subject, text=text, html=html)
        return
    if provider == "mailjet":
        _send_with_mailjet(user, subject=subject, text=text, html=html)
        return
    _send_with_smtp(user, subject=subject, text=text, html=html)


def send_otp_code(user: User, code: str, expires_minutes: int) -> None:
    text = (
        f"Bonjour {user.full_name},\n\n"
        f"Votre code de connexion SaaS Gestion Data est : {code}\n"
        f"Il expire dans {expires_minutes} minutes.\n\n"
        "Si vous n'êtes pas à l'origine de cette tentative, ignorez cet e-mail."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#0f172a">
      <h2 style="margin:0 0 12px">Code de connexion</h2>
      <p>Bonjour {user.full_name},</p>
      <p>Utilisez le code suivant pour finaliser votre connexion à SaaS Gestion Data.</p>
      <div style="font-size:28px;font-weight:700;letter-spacing:6px;background:#f1f5f9;border-radius:12px;padding:18px;text-align:center;margin:20px 0">
        {code}
      </div>
      <p style="font-size:14px;color:#475569">Ce code expire dans {expires_minutes} minutes.</p>
      <p style="font-size:13px;color:#64748b">Si vous n'êtes pas à l'origine de cette tentative, ignorez cet e-mail.</p>
    </div>
    """
    _send_code_email(
        user,
        subject="Votre code de connexion SaaS Gestion Data",
        text=text,
        html=html,
    )


def send_email_verification_code(user: User, code: str, expires_minutes: int) -> None:
    text = (
        f"Bonjour {user.full_name},\n\n"
        f"Votre code de vérification e-mail SaaS Gestion Data est : {code}\n"
        f"Il expire dans {expires_minutes} minutes.\n\n"
        "Si vous n'avez pas créé ce compte, ignorez cet e-mail."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#0f172a">
      <h2 style="margin:0 0 12px">Confirmez votre e-mail</h2>
      <p>Bonjour {user.full_name},</p>
      <p>Utilisez ce code pour activer votre compte SaaS Gestion Data.</p>
      <div style="font-size:28px;font-weight:700;letter-spacing:6px;background:#ecfeff;border-radius:12px;padding:18px;text-align:center;margin:20px 0;color:#0f766e">
        {code}
      </div>
      <p style="font-size:14px;color:#475569">Ce code expire dans {expires_minutes} minutes.</p>
      <p style="font-size:13px;color:#64748b">Si vous n'avez pas créé ce compte, ignorez cet e-mail.</p>
    </div>
    """
    _send_code_email(
        user,
        subject="Confirmez votre e-mail SaaS Gestion Data",
        text=text,
        html=html,
    )


def send_password_reset_code(user: User, code: str, expires_minutes: int) -> None:
    text = (
        f"Bonjour {user.full_name},\n\n"
        f"Votre code de réinitialisation SaaS Gestion Data est : {code}\n"
        f"Il expire dans {expires_minutes} minutes.\n\n"
        "Si vous n'avez pas demandé ce changement, ignorez cet e-mail."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#0f172a">
      <h2 style="margin:0 0 12px">Réinitialisation du mot de passe</h2>
      <p>Bonjour {user.full_name},</p>
      <p>Utilisez ce code pour définir un nouveau mot de passe SaaS Gestion Data.</p>
      <div style="font-size:28px;font-weight:700;letter-spacing:6px;background:#fef3c7;border-radius:12px;padding:18px;text-align:center;margin:20px 0;color:#92400e">
        {code}
      </div>
      <p style="font-size:14px;color:#475569">Ce code expire dans {expires_minutes} minutes.</p>
      <p style="font-size:13px;color:#64748b">Si vous n'avez pas demandé ce changement, ignorez cet e-mail.</p>
    </div>
    """
    _send_code_email(
        user,
        subject="Réinitialisation de votre mot de passe SaaS Gestion Data",
        text=text,
        html=html,
    )
