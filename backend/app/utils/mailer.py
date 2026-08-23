"""Envoi d'e-mails via SMTP.

Utilise la bibliothèque standard (`smtplib`) : aucune dépendance
supplémentaire. L'envoi est bloquant, il est donc déporté dans un thread
pour ne pas figer la boucle asyncio.
"""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate

from app.config import get_settings


class MailNotConfigured(RuntimeError):
    """Levée quand aucun serveur SMTP n'est renseigné."""


def mail_enabled() -> bool:
    return bool(get_settings().smtp_host)


def recipients() -> list[str]:
    """Liste des destinataires configurés (séparés par des virgules)."""
    raw = get_settings().digest_recipients or ""
    return [a.strip() for a in raw.replace(";", ",").split(",") if a.strip()]


def _send_sync(subject: str, html: str, text: str, to: list[str]) -> None:
    s = get_settings()
    if not s.smtp_host:
        raise MailNotConfigured("Aucun serveur SMTP configuré (SMTP_HOST)")
    if not to:
        raise MailNotConfigured("Aucun destinataire configuré (DIGEST_RECIPIENTS)")

    sender = s.smtp_from or s.smtp_user or "rucher@localhost"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Rucher Manager", sender))
    msg["To"] = ", ".join(to)
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    mode = (s.smtp_tls or "starttls").lower()
    if mode == "ssl":
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=context, timeout=30) as srv:
            if s.smtp_user:
                srv.login(s.smtp_user, s.smtp_password)
            srv.send_message(msg)
    else:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30) as srv:
            srv.ehlo()
            if mode == "starttls":
                srv.starttls(context=ssl.create_default_context())
                srv.ehlo()
            if s.smtp_user:
                srv.login(s.smtp_user, s.smtp_password)
            srv.send_message(msg)


async def send_mail(subject: str, html: str, text: str, to: list[str] | None = None) -> list[str]:
    """Envoie un e-mail. Renvoie la liste des destinataires servis."""
    targets = to if to is not None else recipients()
    await asyncio.to_thread(_send_sync, subject, html, text, targets)
    return targets
