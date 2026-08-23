"""Récapitulatif hebdomadaire de l'activité de l'association.

Rassemble ce qui a été fait sur une période (7 jours par défaut) et produit
un e-mail en HTML + texte brut.
"""

from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.apiary import Hive
from app.models.visit import Visit
from app.models.sanitary import SanitaryRecord
from app.models.inventory import InventoryItem, InventoryMovement
from app.models.treasury import Transaction
from app.models.honey import HoneyHarvest, HoneySale
from app.models.event import Event

MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
          "août", "septembre", "octobre", "novembre", "décembre"]


def _fr_date(d: datetime) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def _plural(n: int, singular: str, plural: str | None = None) -> str:
    return f"{n} {singular if n <= 1 else (plural or singular + 's')}"


async def collect(db: AsyncSession, since: datetime, until: datetime) -> dict:
    """Rassemble les chiffres de la période."""
    d: dict = {"since": since, "until": until}

    # ─── Visites ───────────────────────────────────────────────────
    visits = (await db.execute(
        select(Visit).where(Visit.visited_at >= since, Visit.visited_at < until)
        .order_by(desc(Visit.visited_at))
    )).scalars().all()
    d["visits_count"] = len(visits)
    d["alerts"] = [v for v in visits if v.is_alert]
    d["honey_kg"] = round(sum(v.honey_harvest_kg or 0 for v in visits), 1)
    d["pollen_kg"] = round(sum(v.pollen_harvest_kg or 0 for v in visits), 1)

    # Par auteur
    authors: dict[int, int] = {}
    for v in visits:
        authors[v.author_id] = authors.get(v.author_id, 0) + 1
    names = {}
    if authors:
        rows = (await db.execute(select(User).where(User.id.in_(authors.keys())))).scalars().all()
        names = {u.id: f"{u.first_name} {u.last_name}".strip() or u.email for u in rows}
    d["by_author"] = sorted(
        ((names.get(uid, f"#{uid}"), n) for uid, n in authors.items()),
        key=lambda t: -t[1],
    )

    # Ruches concernées (noms, pour les alertes)
    hive_ids = {v.hive_id for v in visits}
    hives = {}
    if hive_ids:
        rows = (await db.execute(select(Hive).where(Hive.id.in_(hive_ids)))).scalars().all()
        hives = {h.id: (h.name or h.napi_number or f"Ruche #{h.id}") for h in rows}
    d["hive_names"] = hives

    # ─── Sanitaire ─────────────────────────────────────────────────
    records = (await db.execute(
        select(SanitaryRecord).where(
            SanitaryRecord.created_at >= since, SanitaryRecord.created_at < until)
    )).scalars().all()
    d["treatments"] = [r for r in records if (r.record_type or "") == "treatment"]
    d["varroa_counts"] = [r for r in records if (r.record_type or "") == "varroa_count"]

    # ─── Inventaire ────────────────────────────────────────────────
    movements = (await db.execute(
        select(InventoryMovement).where(
            InventoryMovement.performed_at >= since, InventoryMovement.performed_at < until)
    )).scalars().all()
    d["mvt_in"] = sum(1 for m in movements if str(getattr(m.movement_type, "value", m.movement_type)) == "in")
    d["mvt_out"] = len(movements) - d["mvt_in"]
    d["low_stock"] = (await db.execute(
        select(InventoryItem).where(
            InventoryItem.alert_threshold.isnot(None),
            InventoryItem.quantity <= InventoryItem.alert_threshold)
    )).scalars().all()

    # ─── Trésorerie ────────────────────────────────────────────────
    txs = (await db.execute(
        select(Transaction).where(Transaction.date >= since, Transaction.date < until)
    )).scalars().all()
    d["income"] = round(sum(t.amount for t in txs
                            if str(getattr(t.transaction_type, "value", t.transaction_type)) == "income"), 2)
    d["expense"] = round(sum(t.amount for t in txs
                             if str(getattr(t.transaction_type, "value", t.transaction_type)) == "expense"), 2)
    d["tx_count"] = len(txs)

    # ─── Miellée ───────────────────────────────────────────────────
    harvests = (await db.execute(
        select(HoneyHarvest).where(
            HoneyHarvest.harvest_date >= since, HoneyHarvest.harvest_date < until)
    )).scalars().all()
    d["harvest_kg"] = round(sum(h.quantity_kg or 0 for h in harvests), 1)
    d["harvest_count"] = len(harvests)

    sales = (await db.execute(
        select(HoneySale).where(HoneySale.sold_at >= since, HoneySale.sold_at < until)
    )).scalars().all()
    d["sales_count"] = len(sales)
    d["sales_amount"] = round(sum(s.total_amount or 0 for s in sales), 2)

    # ─── Événements ────────────────────────────────────────────────
    d["events_upcoming"] = (await db.execute(
        select(Event).where(Event.start_at >= until, Event.start_at < until + timedelta(days=14))
        .order_by(Event.start_at)
    )).scalars().all()

    # ─── Nouveaux comptes ──────────────────────────────────────────
    d["new_users"] = (await db.execute(
        select(func.count()).select_from(User)
        .where(User.created_at >= since, User.created_at < until)
    )).scalar() or 0

    return d


def _has_activity(d: dict) -> bool:
    return any([
        d["visits_count"], d["treatments"], d["varroa_counts"],
        d["mvt_in"], d["mvt_out"], d["tx_count"],
        d["harvest_count"], d["sales_count"], d["new_users"],
    ])


def render(d: dict, base_url: str = "") -> tuple[str, str, str]:
    """Renvoie (sujet, html, texte)."""
    period = f"du {_fr_date(d['since'])} au {_fr_date(d['until'] - timedelta(days=1))}"
    subject = f"Rucher — récapitulatif {period}"

    # ─── Texte brut ────────────────────────────────────────────────
    L = [f"RUCHER MANAGER — récapitulatif {period}", ""]
    if not _has_activity(d):
        L.append("Aucune activité enregistrée cette semaine.")
    else:
        L.append(f"Visites : {d['visits_count']}")
        for name, n in d["by_author"]:
            L.append(f"  - {name} : {_plural(n, 'visite')}")
        if d["alerts"]:
            L.append(f"Alertes : {len(d['alerts'])}")
            for v in d["alerts"][:10]:
                L.append(f"  ! {d['hive_names'].get(v.hive_id, 'Ruche')} — {v.alert_message or 'à vérifier'}")
        if d["honey_kg"] or d["pollen_kg"]:
            L.append(f"Récolte en visite : {d['honey_kg']} kg de miel, {d['pollen_kg']} kg de pollen")
        if d["treatments"] or d["varroa_counts"]:
            L.append(f"Sanitaire : {_plural(len(d['treatments']), 'traitement')}, "
                     f"{_plural(len(d['varroa_counts']), 'comptage')}")
        if d["mvt_in"] or d["mvt_out"]:
            L.append(f"Inventaire : {d['mvt_in']} entrée(s), {d['mvt_out']} sortie(s)")
        if d["low_stock"]:
            L.append(f"Stocks bas : {len(d['low_stock'])}")
            for i in d["low_stock"][:10]:
                L.append(f"  - {i.name} : {i.quantity} {i.unit} (seuil {i.alert_threshold})")
        if d["tx_count"]:
            L.append(f"Trésorerie : +{d['income']:.2f} EUR / -{d['expense']:.2f} EUR "
                     f"(solde de la semaine : {d['income'] - d['expense']:+.2f} EUR)")
        if d["harvest_count"]:
            L.append(f"Miellée : {_plural(d['harvest_count'], 'récolte')}, {d['harvest_kg']} kg")
        if d["sales_count"]:
            L.append(f"Ventes : {_plural(d['sales_count'], 'vente')}, {d['sales_amount']:.2f} EUR")
        if d["new_users"]:
            L.append(f"Nouveaux comptes : {d['new_users']}")
    if d["events_upcoming"]:
        L += ["", "À VENIR (15 jours) :"]
        for e in d["events_upcoming"]:
            L.append(f"  - {e.start_at.strftime('%d/%m %H:%M')} — {e.title}")
    text = "\n".join(L)

    # ─── HTML ──────────────────────────────────────────────────────
    def card(label, value, sub=""):
        return (
            '<td style="padding:6px;" width="33%">'
            '<div style="border:1px solid #e6ddcd;border-radius:12px;padding:14px;background:#fff;">'
            f'<div style="font-size:22px;font-weight:700;color:#9A6B0F;letter-spacing:-.02em;">{value}</div>'
            f'<div style="font-size:12px;color:#7B6A5C;margin-top:2px;">{label}</div>'
            + (f'<div style="font-size:11px;color:#9b8d80;margin-top:2px;">{sub}</div>' if sub else '')
            + '</div></td>'
        )

    def section(title, inner):
        return (
            f'<h2 style="font-size:15px;margin:26px 0 10px;color:#2B2520;'
            f'border-bottom:1px solid #e6ddcd;padding-bottom:6px;">{title}</h2>{inner}'
        )

    def li(txt):
        return f'<li style="margin:4px 0;color:#4E443A;">{txt}</li>'

    parts = []
    if not _has_activity(d):
        parts.append('<p style="color:#7B6A5C;">Aucune activité enregistrée cette semaine.</p>')
    else:
        parts.append(
            '<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;"><tr>'
            + card("Visites", d["visits_count"])
            + card("Alertes", len(d["alerts"]))
            + card("Miel récolté", f"{d['harvest_kg'] or d['honey_kg']} kg")
            + '</tr></table>'
        )

        if d["by_author"]:
            rows = "".join(li(f"<b>{n}</b> — {_plural(c, 'visite')}") for n, c in d["by_author"])
            parts.append(section("Qui a visité", f'<ul style="margin:0;padding-left:18px;">{rows}</ul>'))

        if d["alerts"]:
            rows = "".join(
                li(f'<b style="color:#B3261E;">{d["hive_names"].get(v.hive_id, "Ruche")}</b> — '
                   f'{v.alert_message or "à vérifier"}')
                for v in d["alerts"][:10]
            )
            parts.append(section("Alertes signalées", f'<ul style="margin:0;padding-left:18px;">{rows}</ul>'))

        if d["treatments"] or d["varroa_counts"]:
            rows = ""
            if d["treatments"]:
                rows += li(f"{_plural(len(d['treatments']), 'traitement')} enregistré(s)")
            if d["varroa_counts"]:
                rows += li(f"{_plural(len(d['varroa_counts']), 'comptage')} varroa")
            parts.append(section("Suivi sanitaire", f'<ul style="margin:0;padding-left:18px;">{rows}</ul>'))

        if d["mvt_in"] or d["mvt_out"] or d["low_stock"]:
            rows = ""
            if d["mvt_in"] or d["mvt_out"]:
                rows += li(f"{d['mvt_in']} entrée(s) · {d['mvt_out']} sortie(s) de stock")
            for i in d["low_stock"][:10]:
                rows += li(f'<span style="color:#B26A00;">Stock bas</span> — {i.name} : '
                           f'{i.quantity} {i.unit} (seuil {i.alert_threshold})')
            parts.append(section("Inventaire", f'<ul style="margin:0;padding-left:18px;">{rows}</ul>'))

        if d["tx_count"] or d["sales_count"]:
            balance = d["income"] - d["expense"]
            rows = ""
            if d["tx_count"]:
                rows += li(f"Recettes {d['income']:.2f} € · Dépenses {d['expense']:.2f} € · "
                           f"<b>Solde {balance:+.2f} €</b>")
            if d["sales_count"]:
                rows += li(f"{_plural(d['sales_count'], 'vente')} de miel — {d['sales_amount']:.2f} €")
            parts.append(section("Trésorerie", f'<ul style="margin:0;padding-left:18px;">{rows}</ul>'))

        if d["harvest_count"]:
            hv = _plural(d["harvest_count"], "récolte")
            row = li(f'{hv} — {d["harvest_kg"]} kg')
            parts.append(section("Miellée", f'<ul style="margin:0;padding-left:18px;">{row}</ul>'))

    if d["events_upcoming"]:
        rows = "".join(
            li(f'<b>{e.start_at.strftime("%d/%m à %Hh%M")}</b> — {e.title}'
               + (f' <span style="color:#7B6A5C;">({e.location})</span>' if e.location else ''))
            for e in d["events_upcoming"]
        )
        parts.append(section("À venir (15 jours)", f'<ul style="margin:0;padding-left:18px;">{rows}</ul>'))

    link = (f'<p style="margin-top:28px;text-align:center;">'
            f'<a href="{base_url}" style="background:#9A6B0F;color:#fff;text-decoration:none;'
            f'padding:11px 22px;border-radius:10px;font-weight:600;font-size:14px;'
            f'display:inline-block;">Ouvrir l\'application</a></p>') if base_url else ""

    html = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#FBF7F0;
 font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:24px 16px;">
  <div style="text-align:center;margin-bottom:8px;">
    <div style="font-size:26px;">🐝</div>
    <h1 style="font-size:19px;margin:6px 0 2px;color:#2B2520;letter-spacing:-.02em;">
      Récapitulatif de la semaine</h1>
    <div style="font-size:13px;color:#7B6A5C;">{period}</div>
  </div>
  {''.join(parts)}
  {link}
  <p style="margin-top:26px;font-size:11px;color:#9b8d80;text-align:center;line-height:1.5;">
    Message automatique de Rucher Manager.<br>
    Pour ne plus le recevoir, retirez votre adresse de <code>DIGEST_RECIPIENTS</code>.
  </p>
</div></body></html>"""

    return subject, html, text
