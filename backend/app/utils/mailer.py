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


def env_config() -> dict:
    """Configuration issue des variables d'environnement (.env)."""
    s = get_settings()
    return {
        "smtp_host": s.smtp_host, "smtp_port": s.smtp_port,
        "smtp_user": s.smtp_user, "smtp_password": s.smtp_password,
        "smtp_from": s.smtp_from, "smtp_tls": s.smtp_tls,
        "recipients": s.digest_recipients,
        "digest_enabled": s.digest_enabled,
        "digest_weekday": s.digest_weekday, "digest_hour": s.digest_hour,
        "app_base_url": s.app_base_url,
        "source": "env",
    }


def mail_enabled(cfg: dict | None = None) -> bool:
    return bool((cfg or env_config()).get("smtp_host"))


def parse_recipients(raw: str | None) -> list[str]:
    """Découpe une liste d'adresses séparées par des virgules ou points-virgules."""
    return [a.strip() for a in (raw or "").replace(";", ",").split(",") if a.strip()]


def recipients(cfg: dict | None = None) -> list[str]:
    return parse_recipients((cfg or env_config()).get("recipients"))


def _send_sync(subject: str, html: str, text: str, to: list[str], cfg: dict) -> None:
    class _C:
        smtp_host = cfg.get("smtp_host") or ""
        smtp_port = int(cfg.get("smtp_port") or 587)
        smtp_user = cfg.get("smtp_user") or ""
        smtp_password = cfg.get("smtp_password") or ""
        smtp_from = cfg.get("smtp_from") or ""
        smtp_tls = cfg.get("smtp_tls") or "starttls"
    s = _C()
    if not s.smtp_host:
        raise MailNotConfigured("Aucun serveur SMTP configuré")
    if not to:
        raise MailNotConfigured("Aucun destinataire configuré")

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


async def send_mail(subject: str, html: str, text: str,
                    to: list[str] | None = None, cfg: dict | None = None) -> list[str]:
    """Envoie un e-mail. Renvoie la liste des destinataires servis."""
    conf = cfg or env_config()
    targets = to if to is not None else recipients(conf)
    await asyncio.to_thread(_send_sync, subject, html, text, targets, conf)
    return targets
