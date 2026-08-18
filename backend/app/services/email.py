import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.models.user import User


class EmailDeliveryError(Exception):
    pass


def _send_code_email(user: User, *, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        raise EmailDeliveryError("Service e-mail OTP non configuré.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
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
