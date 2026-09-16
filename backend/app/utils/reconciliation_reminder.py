"""Rappel : le rapprochement bancaire du mois écoulé est-il fait ?

Un rapprochement qu'on ne fait pas ne se signale jamais de lui-même. On s'en
aperçoit à la clôture, quand il faut remonter six mois d'écritures pour
retrouver l'écart. Ce rappel prévient le trésorier et les administrateurs tant
que le mois précédent n'est pas validé — une fois par semaine, pas tous les
jours : un rappel quotidien finit par être ignoré.
"""

from datetime import datetime

from sqlalchemy import select

from app.database import async_session
from app.models.notification import AppSetting
from app.models.treasury import Transaction, BankReconciliation
from app.models.user import User, UserRole, RoleEnum
from app.utils.push import notify_users

MARQUEUR = "reconciliation_reminder_last"
MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre")

# Laisser le temps de recevoir le relevé : rappeler le 1er du mois n'aurait
# aucun sens, la banque n'a pas encore arrêté le mois précédent.
JOUR_MINIMUM = 5


def _mois_precedent(maintenant: datetime) -> tuple[int, int]:
    return (maintenant.year - 1, 12) if maintenant.month == 1 else (maintenant.year, maintenant.month - 1)


def _bornes(annee: int, mois: int) -> tuple[datetime, datetime]:
    return datetime(annee, mois, 1), datetime(annee + (mois == 12), (mois % 12) + 1, 1)


def _semaine(maintenant: datetime) -> str:
    a, s, _ = maintenant.isocalendar()
    return f"{a}-W{s:02d}"


async def check_once(maintenant: datetime | None = None) -> int:
    """Envoie le rappel si nécessaire ; renvoie le nombre de destinataires."""
    maintenant = maintenant or datetime.utcnow()
    if maintenant.day < JOUR_MINIMUM:
        return 0

    annee, mois = _mois_precedent(maintenant)
    libelle = f"{MOIS_FR[mois - 1]} {annee}"

    async with async_session() as db:
        res = await db.execute(
            select(BankReconciliation).where(BankReconciliation.year == annee,
                                             BankReconciliation.month == mois)
        )
        rec = res.scalar_one_or_none()
        if rec and rec.validated:
            return 0

        debut, fin = _bornes(annee, mois)
        r = await db.execute(
            select(Transaction).where(Transaction.date >= debut, Transaction.date < fin)
        )
        lignes = list(r.scalars().all())
        # Un mois sans la moindre écriture n'a rien à rapprocher : relancer
        # pour du vide use le rappel jusqu'à ce qu'on ne le lise plus.
        if not lignes:
            return 0
        restant = sum(1 for t in lignes if t.reconciled_at is None)

        # Une seule relance par semaine, même si le conteneur redémarre.
        semaine = _semaine(maintenant)
        marqueur = f"{annee}-{mois:02d}:{semaine}"
        ligne = await db.get(AppSetting, MARQUEUR)
        if ligne and ligne.value == marqueur:
            return 0
        if ligne:
            ligne.value = marqueur
        else:
            db.add(AppSetting(key=MARQUEUR, value=marqueur))

        res = await db.execute(
            select(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .where(User.is_active.is_(True),
                   UserRole.role.in_([RoleEnum.ADMIN, RoleEnum.TREASURER]))
        )
        destinataires = sorted(set(res.scalars().all()))
        await db.commit()

    if not destinataires:
        return 0

    if restant:
        texte = (f"{restant} écriture(s) restent à pointer sur {len(lignes)}. "
                 "Ouvrez la trésorerie pour terminer le rapprochement.")
    else:
        texte = ("Toutes les écritures sont pointées : il ne reste qu'à saisir "
                 "le solde du relevé et à valider.")

    notify_users(destinataires,
                 f"🏦 Rapprochement bancaire à faire — {libelle}",
                 texte, "/app/treasury", category="treasury")
    print(f"📌 Rappel de rapprochement envoyé pour {libelle} "
          f"à {len(destinataires)} personne(s)")
    return len(destinataires)
