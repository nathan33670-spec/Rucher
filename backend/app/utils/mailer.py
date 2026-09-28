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


def _compose(subject: str, html: str, text: str, to: list[str], sender: str,
             attachments: list[dict] | None = None) -> EmailMessage:
    """Message complet, pièces jointes comprises.

    ``attachments`` : liste de ``{filename, mime_type, content}`` (octets).
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Rucher Manager", sender))
    msg["To"] = ", ".join(to)
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    for piece in attachments or []:
        type_mime = (piece.get("mime_type") or "application/octet-stream")
        principal, _, sous = type_mime.partition("/")
        msg.add_attachment(
            piece["content"],
            maintype=principal or "application",
            subtype=sous or "octet-stream",
            filename=piece.get("filename") or "piece-jointe",
        )
    return msg


class _Conf:
    """Réglages SMTP d'un envoi, lus une fois pour toutes.

    Extrait de « _send_sync », où il était défini en local : l'envoi groupé en
    a besoin aussi, et deux copies auraient fini par diverger.
    """

    def __init__(self, cfg: dict):
        self.smtp_host = cfg.get("smtp_host") or ""
        self.smtp_port = int(cfg.get("smtp_port") or 587)
        self.smtp_user = cfg.get("smtp_user") or ""
        self.smtp_password = cfg.get("smtp_password") or ""
        self.smtp_from = cfg.get("smtp_from") or ""
        self.smtp_tls = cfg.get("smtp_tls") or "starttls"


def _connexion(cfg: dict):
    """Connexion SMTP ouverte, prête à l'envoi.

    Isolée pour qu'un envoi groupé n'ouvre qu'une seule session : ouvrir et
    fermer une connexion par adhérent est lent, et certains serveurs y voient
    un comportement d'expéditeur en masse.
    """
    s = _Conf(cfg)
    mode = (s.smtp_tls or "starttls").lower()
    if mode == "ssl":
        srv = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port,
                               context=ssl.create_default_context(), timeout=30)
    else:
        srv = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30)
        srv.ehlo()
        if mode == "starttls":
            srv.starttls(context=ssl.create_default_context())
            srv.ehlo()
    if s.smtp_user:
        srv.login(s.smtp_user, s.smtp_password)
    return srv


def _send_sync(subject: str, html: str, text: str, to: list[str], cfg: dict,
               attachments: list[dict] | None = None) -> None:
    s = _Conf(cfg)
    if not s.smtp_host:
        raise MailNotConfigured("Aucun serveur SMTP configuré")
    if not to:
        raise MailNotConfigured("Aucun destinataire configuré")

    sender = s.smtp_from or s.smtp_user or "rucher@localhost"

    msg = _compose(subject, html, text, to, sender, attachments)

    srv = _connexion(cfg)
    try:
        srv.send_message(msg)
    finally:
        try:
            srv.quit()
        except Exception:
            pass


async def send_mail(subject: str, html: str, text: str,
                    to: list[str] | None = None, cfg: dict | None = None,
                    attachments: list[dict] | None = None) -> list[str]:
    """Envoie un e-mail. Renvoie la liste des destinataires servis."""
    conf = cfg or env_config()
    targets = to if to is not None else recipients(conf)
    await asyncio.to_thread(_send_sync, subject, html, text, targets, conf, attachments)
    return targets


def _send_bulk_sync(messages: list[dict], cfg: dict) -> list[dict]:
    """Envoie une série de messages sur une seule connexion SMTP.

    Chaque destinataire reçoit son propre message — c'est indispensable dès
    qu'on personnalise le contenu, et c'est aussi ce qui évite d'exposer la
    liste des adresses à tout le monde.

    L'échec d'un destinataire n'arrête pas les autres : on renvoie le détail,
    à charge de l'appelant d'en rendre compte.
    """
    s = _Conf(cfg)
    if not s.smtp_host:
        raise MailNotConfigured("Serveur SMTP non configuré")
    expediteur = s.smtp_from or s.smtp_user or "rucher@localhost"

    resultats: list[dict] = []
    srv = None
    try:
        srv = _connexion(cfg)
        for m in messages:
            try:
                msg = _compose(m["subject"], m["html"], m["text"], [m["to"]],
                               expediteur, m.get("attachments"))
                srv.send_message(msg)
                resultats.append({"to": m["to"], "ok": True, "error": None})
            except Exception as e:
                resultats.append({"to": m["to"], "ok": False, "error": str(e)[:300]})
    finally:
        if srv is not None:
            try:
                srv.quit()
            except Exception:
                pass
    return resultats


async def send_bulk(messages: list[dict], cfg: dict | None = None) -> list[dict]:
    """Envoi groupé, un message par destinataire. Renvoie le détail par adresse."""
    conf = cfg or env_config()
    return await asyncio.to_thread(_send_bulk_sync, messages, conf)
