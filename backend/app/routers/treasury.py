"""Routes — Trésorerie."""

import json
import os
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.treasury import (Transaction, Invoice, TransactionType,
                                 TransactionCategory, BankReconciliation)
from app.models.notification import AppSetting
from app.models.user import User, UserRole, RoleEnum
from app.schemas.treasury import (TransactionCreate, TransactionUpdate, TransactionOut,
                                  SumUpSettings, SumUpSettingsUpdate, ImportResult,
                                  ReconciliationOut, ReconciliationMonth,
                                  ReconciliationUpdate, ReconciliationToggle)
from app.utils.auth import get_current_user, require_roles, get_user_roles
from app.utils.audit import log_action
from app.utils import sumup
from app.routers.settings import load_access


async def _check_read_access(db, user) -> None:
    """La trésorerie est réservée aux admins et trésoriers, sauf si un
    administrateur a ouvert la lecture à tous les membres."""
    roles = get_user_roles(user)
    if RoleEnum.ADMIN.value in roles or RoleEnum.TREASURER.value in roles:
        return
    access = await load_access(db)
    if not access.treasury_read_all:
        raise HTTPException(
            403,
            "La trésorerie est réservée au bureau. Un administrateur peut "
            "l'ouvrir en lecture à tous les membres dans les réglages.",
        )
from app.utils.push import notify, notify_users
from app.config import get_settings

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


@router.get("/", response_model=list[TransactionOut])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _check_read_access(db, user)
    result = await db.execute(select(Transaction).order_by(Transaction.date.desc()).limit(200))
    txs = result.scalars().all()
    return [_tx_out(t) for t in txs]


@router.post("/", response_model=TransactionOut, status_code=201)
async def create_transaction(
    body: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    tx = Transaction(**body.model_dump(exclude_unset=True), created_by=user.id)
    db.add(tx)
    await db.flush()
    await log_action(db, user.id, "create", "transaction", tx.id)
    await db.refresh(tx)
    sens = "Recette" if tx.transaction_type == TransactionType.INCOME else "Dépense"
    notify("treasury", "💶 Trésorerie",
           f"{sens} : {tx.amount:.2f} € — {tx.description or tx.category.value}", "/app/treasury",
           exclude_user_id=user.id)
    return _tx_out(tx)


@router.put("/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id: int, body: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    tx = await db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(404, "Transaction introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(tx, k, v)
    await log_action(db, user.id, "update", "transaction", tx.id)
    return _tx_out(tx)


@router.delete("/{tx_id}", status_code=204)
async def delete_transaction(
    tx_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    tx = await db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(404, "Transaction introuvable")
    await db.delete(tx)
    await log_action(db, user.id, "delete", "transaction", tx_id)


@router.post("/{tx_id}/invoices", status_code=201)
async def upload_invoice(
    tx_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    tx = await db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(404, "Transaction introuvable")

    upload_dir = get_settings().upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    invoice = Invoice(
        transaction_id=tx_id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_path=file_path,
    )
    db.add(invoice)
    await db.flush()
    await log_action(db, user.id, "upload", "invoice", tx_id,
                     details=file.filename)
    return {"id": invoice.id, "filename": invoice.filename}


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _check_read_access(db, user)
    invoice = await db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(404, "Facture introuvable")
    if not os.path.exists(invoice.file_path):
        raise HTTPException(404, "Fichier introuvable sur le serveur")
    return FileResponse(invoice.file_path, filename=invoice.filename, media_type=invoice.mime_type)


@router.get("/summary")
async def annual_summary(
    year: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Bilan annuel simplifié."""
    await _check_read_access(db, user)
    from datetime import datetime
    y = year or datetime.utcnow().year

    income = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.transaction_type == TransactionType.INCOME)
        .where(func.extract("year", Transaction.date) == y)
    )
    expense = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.transaction_type == TransactionType.EXPENSE)
        .where(func.extract("year", Transaction.date) == y)
    )
    total_income = float(income.scalar())
    total_expense = float(expense.scalar())
    return {
        "year": y,
        "income": total_income,
        "expense": total_expense,
        "balance": total_income - total_expense,
    }


def _tx_out(t: Transaction) -> TransactionOut:
    return TransactionOut(
        id=t.id,
        transaction_type=t.transaction_type.value,
        category=t.category.value,
        amount=t.amount,
        description=t.description,
        supplier=t.supplier,
        date=t.date,
        source=t.source,
        reconciled_at=t.reconciled_at,
        created_by=t.created_by,
        invoices=[{"id": inv.id, "filename": inv.filename} for inv in t.invoices],
        created_at=t.created_at,
    )


# ─── Liaison SumUp ────────────────────────────────────────────────────
#
# Deux voies, parce que l'API SumUp n'en couvre qu'une : elle liste les
# paiements **entrants** (c'est une API d'encaisseur), mais ignore le compte
# professionnel. Les dépenses n'arrivent donc que par l'export CSV du relevé.

SUMUP_KEY = "sumup_settings"


async def load_sumup(db: AsyncSession) -> dict:
    cfg = sumup.config_defaults()
    row = await db.get(AppSetting, SUMUP_KEY)
    if row:
        try:
            cfg.update(json.loads(row.value))
        except Exception:
            pass
    return cfg


async def _save_sumup(db: AsyncSession, cfg: dict) -> None:
    row = await db.get(AppSetting, SUMUP_KEY)
    if row:
        row.value = json.dumps(cfg)
    else:
        db.add(AppSetting(key=SUMUP_KEY, value=json.dumps(cfg)))


def _sumup_out(cfg: dict) -> SumUpSettings:
    derniere = cfg.get("last_sync_at")
    try:
        quand = datetime.fromisoformat(derniere) if derniere else None
    except (TypeError, ValueError):
        quand = None
    return SumUpSettings(
        merchant_code=cfg.get("merchant_code") or "",
        lookback_days=int(cfg.get("lookback_days") or sumup.DEFAULT_LOOKBACK_DAYS),
        enabled=bool(cfg.get("enabled")),
        # La clé n'est jamais renvoyée : on dit seulement qu'elle existe.
        api_key_set=bool((cfg.get("api_key") or "").strip()),
        last_sync_at=quand,
    )


@router.get("/sumup/settings", response_model=SumUpSettings)
async def get_sumup_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    return _sumup_out(await load_sumup(db))


@router.put("/sumup/settings", response_model=SumUpSettings)
async def set_sumup_settings(
    body: SumUpSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    cfg = await load_sumup(db)
    donnees = body.model_dump(exclude_unset=True)
    # Clé laissée vide = on conserve celle déjà enregistrée : l'interface ne
    # la relit jamais, la renvoyer vide l'effacerait par mégarde.
    if not (donnees.get("api_key") or "").strip():
        donnees.pop("api_key", None)
    cfg.update({k: v for k, v in donnees.items() if v is not None})
    await _save_sumup(db, cfg)
    await log_action(db, user.id, "update", "sumup_settings", None)
    return _sumup_out(cfg)


async def _enregistre(db, user, lignes: list[dict], categorie) -> ImportResult:
    """Crée les écritures manquantes ; ignore celles déjà importées."""
    res = ImportResult()
    if not lignes:
        return res

    refs = [l["external_ref"] for l in lignes]
    deja = set((await db.execute(
        select(Transaction.external_ref).where(Transaction.external_ref.in_(refs))
    )).scalars().all())

    vues: set[str] = set()
    for ligne in lignes:
        ref = ligne["external_ref"]
        # Le même relevé peut contenir deux lignes identiques : le second
        # exemplaire n'est pas un doublon d'import, on le laisse passer une
        # seule fois par référence.
        if ref in deja or ref in vues:
            res.skipped += 1
            continue
        vues.add(ref)
        db.add(Transaction(
            transaction_type=TransactionType.EXPENSE if ligne["is_expense"] else TransactionType.INCOME,
            category=categorie,
            amount=ligne["amount"],
            description=ligne["description"],
            supplier=ligne.get("supplier"),
            date=ligne["date"],
            source=ligne["source"],
            external_ref=ref,
            created_by=user.id,
        ))
        res.created += 1
        if ligne["is_expense"]:
            res.expense += 1
        else:
            res.income += 1
    await db.flush()
    return res


@router.post("/sumup/sync", response_model=ImportResult)
async def sync_sumup(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Récupère encaissements et commissions SumUp, puis crée le manquant.

    Deux sources, parce qu'une seule ne suffit pas :

    - l'historique des **transactions** donne les encaissements (recettes) et
      les remboursements ;
    - les **virements** donnent les **commissions SumUp** et les retenues, qui
      sont des dépenses et n'apparaissent nulle part ailleurs.

    Restent hors de portée les achats réglés avec la carte du compte
    professionnel : SumUp n'expose ni le compte pro ni ses relevés. C'est
    l'import du relevé (« /sumup/import-csv ») qui prend le relais.

    Rejouable : chaque écriture porte la référence SumUp dont elle provient,
    une seconde synchronisation ne recrée donc rien.
    """
    cfg = await load_sumup(db)
    maintenant = datetime.utcnow()
    depuis = maintenant - timedelta(
        days=int(cfg.get("lookback_days") or sumup.DEFAULT_LOOKBACK_DAYS))
    try:
        ventes = await sumup.fetch_transactions(cfg, depuis)
    except sumup.SumUpError as e:
        raise HTTPException(502, str(e))
    except Exception as e:
        raise HTTPException(502, f"SumUp injoignable : {e}")

    # Les commissions ne doivent pas faire échouer la reprise des recettes :
    # une clé sans la portée « payouts » reste utile pour les encaissements.
    frais: list[dict] = []
    avertissement = ""
    try:
        frais = await sumup.fetch_payouts(cfg, depuis, maintenant)
    except sumup.SumUpError as e:
        avertissement = f" Commissions non reprises : {e}"
    except Exception as e:
        avertissement = f" Commissions non reprises : {e}"

    res = await _enregistre(db, user, ventes, TransactionCategory.HONEY_SALE)
    res_frais = await _enregistre(db, user, frais, TransactionCategory.OTHER)
    res.created += res_frais.created
    res.skipped += res_frais.skipped
    res.income += res_frais.income
    res.expense += res_frais.expense
    if avertissement:
        res.errors.append(avertissement.strip())

    cfg["last_sync_at"] = maintenant.isoformat()
    await _save_sumup(db, cfg)
    await log_action(db, user.id, "sumup_sync", "transaction", None,
                     details=f"{res.created} créée(s), {res.skipped} déjà connue(s)")
    res.detail = (
        f"{res.created} écriture(s) ajoutée(s) — {res.income} recette(s), "
        f"{res.expense} dépense(s) dont les commissions SumUp. "
        f"{res.skipped} déjà connue(s)." + avertissement +
        " Les achats réglés avec la carte du compte professionnel ne sont pas "
        "accessibles par l'API : importez le relevé pour les récupérer."
    )
    return res


@router.post("/sumup/import-csv", response_model=ImportResult)
async def import_sumup_statement(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Import du relevé du compte professionnel SumUp (CSV).

    C'est la seule voie pour les **dépenses** : SumUp n'expose ni le compte
    professionnel, ni les relevés. Le fichier se télécharge depuis le tableau
    de bord SumUp.

    Rejouable : réimporter le même relevé, ou un relevé qui chevauche le
    précédent, ne crée aucun doublon.
    """
    contenu = await file.read()
    try:
        lignes = sumup.parse_statement_csv(contenu)
    except sumup.SumUpError as e:
        raise HTTPException(400, str(e))

    if not lignes:
        raise HTTPException(
            400,
            "Aucune opération lisible dans ce fichier : vérifiez qu'il s'agit "
            "bien de l'export CSV du relevé, et non d'un PDF renommé.",
        )

    res = await _enregistre(db, user, lignes, TransactionCategory.OTHER)
    await log_action(db, user.id, "sumup_import", "transaction", None,
                     details=f"{res.created} créée(s), {res.skipped} déjà connue(s)")
    res.detail = (
        f"{res.created} écriture(s) ajoutée(s) — {res.income} recette(s), "
        f"{res.expense} dépense(s). {res.skipped} opération(s) déjà connue(s). "
        "Pensez à joindre les factures aux dépenses concernées."
    )
    return res


# ─── Rapprochement bancaire ───────────────────────────────────────────
#
# Rapprocher, c'est confronter ce que dit l'association à ce que dit la
# banque. Une écriture « pointée » a été retrouvée sur le relevé ; le solde
# des écritures pointées doit tomber sur le solde du relevé. Tout écart
# signale une écriture manquante d'un côté ou de l'autre — c'est justement ce
# qu'on cherche.

MOIS_FR = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre")


def _libelle_mois(annee: int, mois: int) -> str:
    return f"{MOIS_FR[mois - 1]} {annee}"


def _bornes(annee: int, mois: int) -> tuple[datetime, datetime]:
    debut = datetime(annee, mois, 1)
    fin = datetime(annee + (mois == 12), (mois % 12) + 1, 1)
    return debut, fin


def _signe(t: Transaction) -> float:
    """Montant signé : une dépense diminue le solde."""
    return -t.amount if t.transaction_type == TransactionType.EXPENSE else t.amount


def _valide_periode(annee: int, mois: int) -> None:
    if not 1 <= mois <= 12:
        raise HTTPException(400, "Mois invalide (1 à 12).")
    if not 2000 <= annee <= 2100:
        raise HTTPException(400, "Année invalide.")


async def _get_or_create_reconciliation(db: AsyncSession, annee: int, mois: int) -> BankReconciliation:
    res = await db.execute(
        select(BankReconciliation).where(BankReconciliation.year == annee,
                                         BankReconciliation.month == mois)
    )
    rec = res.scalar_one_or_none()
    if rec is None:
        rec = BankReconciliation(year=annee, month=mois)
        db.add(rec)
        await db.flush()
    return rec


async def _solde_anterieur(db: AsyncSession, debut: datetime) -> float:
    """Solde des écritures pointées antérieures au mois.

    C'est le point de départ du rapprochement : sans lui, on comparerait le
    mouvement du mois à un solde de relevé qui, lui, est cumulé.
    """
    res = await db.execute(
        select(Transaction).where(Transaction.date < debut,
                                  Transaction.reconciled_at.isnot(None))
    )
    return round(sum(_signe(t) for t in res.scalars().all()), 2)


@router.get("/reconciliation", response_model=list[ReconciliationMonth])
async def list_reconciliations(
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Suivi mois par mois : où en est le rapprochement ?

    Renvoie les derniers mois, **plus tout mois antérieur qui porte des
    écritures sans être validé**. Sans ce rattrapage, un mois oublié
    sortirait de la fenêtre et ne se rappellerait plus jamais à personne —
    exactement ce qu'un suivi de rapprochement doit empêcher.
    """
    months = max(1, min(int(months or 12), 60))
    aujourdhui = datetime.utcnow()
    res = await db.execute(select(BankReconciliation))
    connus = {(r.year, r.month): r for r in res.scalars().all()}

    # Fenêtre récente.
    periodes: list[tuple[int, int]] = []
    annee, mois = aujourdhui.year, aujourdhui.month
    for _ in range(months):
        periodes.append((annee, mois))
        mois -= 1
        if mois == 0:
            annee, mois = annee - 1, 12

    # Rattrapage : les mois plus anciens qui portent des écritures et ne sont
    # pas validés. Un mois validé, lui, peut sortir de la vue sans dommage.
    r = await db.execute(
        select(func.extract("year", Transaction.date),
               func.extract("month", Transaction.date))
        .group_by(func.extract("year", Transaction.date),
                  func.extract("month", Transaction.date))
    )
    for an, mo in r.all():
        cle = (int(an), int(mo))
        if cle in periodes:
            continue
        rec = connus.get(cle)
        if rec and rec.validated:
            continue
        periodes.append(cle)

    periodes.sort(reverse=True)

    sorties = []
    for annee, mois in periodes:
        debut, fin = _bornes(annee, mois)
        r = await db.execute(
            select(Transaction).where(Transaction.date >= debut, Transaction.date < fin)
        )
        lignes = list(r.scalars().all())
        pointees = [t for t in lignes if t.reconciled_at is not None]
        rec = connus.get((annee, mois))
        sorties.append(ReconciliationMonth(
            year=annee, month=mois, label=_libelle_mois(annee, mois),
            validated=bool(rec and rec.validated),
            validated_at=rec.validated_at if rec else None,
            total=len(lignes), reconciled=len(pointees),
            pending=len(lignes) - len(pointees),
        ))
    return sorties


@router.get("/reconciliation/{annee}/{mois}", response_model=ReconciliationOut)
async def get_reconciliation(
    annee: int, mois: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Le mois à rapprocher : ses écritures, ses soldes, son écart."""
    _valide_periode(annee, mois)
    debut, fin = _bornes(annee, mois)

    res = await db.execute(
        select(BankReconciliation).where(BankReconciliation.year == annee,
                                         BankReconciliation.month == mois)
    )
    rec = res.scalar_one_or_none()

    r = await db.execute(
        select(Transaction)
        .where(Transaction.date >= debut, Transaction.date < fin)
        .order_by(Transaction.date.asc(), Transaction.id.asc())
    )
    lignes = list(r.scalars().all())
    pointees = [t for t in lignes if t.reconciled_at is not None]
    attente = [t for t in lignes if t.reconciled_at is None]

    ouverture = await _solde_anterieur(db, debut)
    total_pointe = round(sum(_signe(t) for t in pointees), 2)
    solde_pointe = round(ouverture + total_pointe, 2)

    nom_valideur = None
    if rec and rec.validated_by:
        u = await db.get(User, rec.validated_by)
        if u:
            nom_valideur = f"{u.first_name} {u.last_name}".strip() or u.email

    releve = rec.statement_balance if rec else None
    return ReconciliationOut(
        year=annee, month=mois, label=_libelle_mois(annee, mois),
        validated=bool(rec and rec.validated),
        validated_at=rec.validated_at if rec else None,
        validated_by_name=nom_valideur,
        statement_balance=releve,
        notes=rec.notes if rec else None,
        opening_balance=ouverture,
        reconciled_total=total_pointe,
        reconciled_balance=solde_pointe,
        pending_total=round(sum(_signe(t) for t in attente), 2),
        difference=round(releve - solde_pointe, 2) if releve is not None else None,
        counts={"total": len(lignes), "reconciled": len(pointees), "pending": len(attente)},
        transactions=[_tx_out(t) for t in lignes],
    )


@router.put("/reconciliation/{annee}/{mois}", response_model=ReconciliationOut)
async def update_reconciliation(
    annee: int, mois: int, body: ReconciliationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Enregistre le solde du relevé bancaire et les remarques du mois."""
    _valide_periode(annee, mois)
    rec = await _get_or_create_reconciliation(db, annee, mois)
    if rec.validated:
        raise HTTPException(
            409,
            f"Le rapprochement de {_libelle_mois(annee, mois)} est validé : "
            "rouvrez-le avant de le modifier.",
        )
    donnees = body.model_dump(exclude_unset=True)
    for champ, valeur in donnees.items():
        setattr(rec, champ, valeur)
    await db.flush()
    return await get_reconciliation(annee, mois, db, user)


@router.post("/reconciliation/{annee}/{mois}/pointer", response_model=ReconciliationOut)
async def toggle_reconciliation(
    annee: int, mois: int, body: ReconciliationToggle,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Pointe ou dépointe des écritures du mois."""
    _valide_periode(annee, mois)
    debut, fin = _bornes(annee, mois)

    res = await db.execute(
        select(BankReconciliation).where(BankReconciliation.year == annee,
                                         BankReconciliation.month == mois)
    )
    rec = res.scalar_one_or_none()
    if rec and rec.validated:
        raise HTTPException(
            409,
            f"Le rapprochement de {_libelle_mois(annee, mois)} est validé : "
            "rouvrez-le pour modifier le pointage.",
        )

    if not body.transaction_ids:
        raise HTTPException(400, "Aucune écriture désignée.")

    r = await db.execute(
        select(Transaction).where(Transaction.id.in_(body.transaction_ids))
    )
    lignes = list(r.scalars().all())
    maintenant = datetime.utcnow()
    for t in lignes:
        # Une écriture d'un autre mois n'a rien à faire dans ce rapprochement :
        # la pointer ici fausserait le solde des deux mois.
        if not (debut <= t.date < fin):
            raise HTTPException(
                400,
                f"L'écriture « {t.description or t.id} » n'appartient pas à "
                f"{_libelle_mois(annee, mois)}.",
            )
        t.reconciled_at = maintenant if body.reconciled else None
    await db.flush()
    return await get_reconciliation(annee, mois, db, user)


@router.post("/reconciliation/{annee}/{mois}/valider", response_model=ReconciliationOut)
async def validate_reconciliation(
    annee: int, mois: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.TREASURER)),
):
    """Valide le rapprochement du mois et prévient les administrateurs.

    Refusé tant qu'un écart subsiste ou qu'une écriture reste à pointer : un
    rapprochement validé avec un écart ne vaut rien, et laisserait croire que
    les comptes sont justes.
    """
    _valide_periode(annee, mois)
    debut, fin = _bornes(annee, mois)
    rec = await _get_or_create_reconciliation(db, annee, mois)
    if rec.validated:
        raise HTTPException(409, f"Le rapprochement de {_libelle_mois(annee, mois)} est déjà validé.")
    if rec.statement_balance is None:
        raise HTTPException(
            400,
            "Renseignez d'abord le solde du relevé bancaire à la fin du mois : "
            "sans lui, il n'y a rien à rapprocher.",
        )

    r = await db.execute(
        select(Transaction).where(Transaction.date >= debut, Transaction.date < fin)
    )
    lignes = list(r.scalars().all())
    attente = [t for t in lignes if t.reconciled_at is None]
    if attente:
        raise HTTPException(
            400,
            f"{len(attente)} écriture(s) ne sont pas encore pointées : "
            "retrouvez-les sur le relevé, ou corrigez-les, avant de valider.",
        )

    ouverture = await _solde_anterieur(db, debut)
    solde_pointe = round(ouverture + sum(_signe(t) for t in lignes), 2)
    ecart = round(rec.statement_balance - solde_pointe, 2)
    if abs(ecart) >= 0.01:
        raise HTTPException(
            400,
            f"Écart de {ecart:+.2f} € entre le relevé ({rec.statement_balance:.2f} €) "
            f"et les écritures pointées ({solde_pointe:.2f} €). Il manque une "
            "écriture d'un côté ou de l'autre : le rapprochement ne peut pas "
            "être validé tant qu'il subsiste.",
        )

    rec.validated = True
    rec.validated_by = user.id
    rec.validated_at = datetime.utcnow()
    rec.reconciled_balance = solde_pointe
    for t in lignes:
        t.reconciliation_id = rec.id
    await db.flush()

    qui = f"{user.first_name} {user.last_name}".strip() or user.email
    libelle = _libelle_mois(annee, mois)
    await log_action(db, user.id, "reconciliation_validated", "treasury", rec.id,
                     details=f"{libelle} — solde {solde_pointe:.2f} €")

    # Les administrateurs répondent des comptes : ils doivent savoir qu'un
    # mois est arrêté, sans avoir à aller le vérifier.
    res = await db.execute(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .where(User.is_active.is_(True), UserRole.role == RoleEnum.ADMIN)
    )
    admins = [uid for uid in set(res.scalars().all()) if uid != user.id]
    if admins:
        notify_users(
            admins,
            f"✅ Rapprochement bancaire validé — {libelle}",
            f"{qui} a validé le rapprochement de {libelle} : "
            f"{len(lignes)} écriture(s) pointée(s), solde {solde_pointe:.2f} € "
            "conforme au relevé.",
            "/app/treasury",
            category="treasury",
        )

    return await get_reconciliation(annee, mois, db, user)


@router.post("/reconciliation/{annee}/{mois}/rouvrir", response_model=ReconciliationOut)
async def reopen_reconciliation(
    annee: int, mois: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Rouvre un mois validé — réservé aux administrateurs.

    Un mois arrêté ne se rouvre pas à la légère : la réouverture est inscrite
    au journal, et les administrateurs en sont avertis.
    """
    _valide_periode(annee, mois)
    res = await db.execute(
        select(BankReconciliation).where(BankReconciliation.year == annee,
                                         BankReconciliation.month == mois)
    )
    rec = res.scalar_one_or_none()
    if not rec or not rec.validated:
        raise HTTPException(400, f"Le rapprochement de {_libelle_mois(annee, mois)} n'est pas validé.")

    rec.validated = False
    rec.validated_by = None
    rec.validated_at = None
    debut, fin = _bornes(annee, mois)
    r = await db.execute(
        select(Transaction).where(Transaction.date >= debut, Transaction.date < fin)
    )
    for t in r.scalars().all():
        t.reconciliation_id = None
    await db.flush()

    qui = f"{user.first_name} {user.last_name}".strip() or user.email
    libelle = _libelle_mois(annee, mois)
    await log_action(db, user.id, "reconciliation_reopened", "treasury", rec.id,
                     details=libelle)
    res = await db.execute(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .where(User.is_active.is_(True), UserRole.role == RoleEnum.ADMIN)
    )
    admins = [uid for uid in set(res.scalars().all()) if uid != user.id]
    if admins:
        notify_users(admins, f"⚠️ Rapprochement rouvert — {libelle}",
                     f"{qui} a rouvert le rapprochement de {libelle}.",
                     "/app/treasury", category="treasury")
    return await get_reconciliation(annee, mois, db, user)
