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
                                 TransactionCategory)
from app.models.notification import AppSetting
from app.models.user import User, RoleEnum
from app.schemas.treasury import (TransactionCreate, TransactionUpdate, TransactionOut,
                                  SumUpSettings, SumUpSettingsUpdate, ImportResult)
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
from app.utils.push import notify
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
    """Récupère les encaissements SumUp et crée les écritures manquantes.

    Ne concerne que les **recettes** : l'API SumUp ne connaît pas les achats
    réglés avec la carte du compte professionnel. Pour les dépenses, c'est
    l'import du relevé (« /sumup/import-csv ») qui prend le relais.

    Rejouable : chaque écriture porte la référence SumUp dont elle provient,
    une seconde synchronisation ne recrée donc rien.
    """
    cfg = await load_sumup(db)
    depuis = datetime.utcnow() - timedelta(
        days=int(cfg.get("lookback_days") or sumup.DEFAULT_LOOKBACK_DAYS))
    try:
        lignes = await sumup.fetch_transactions(cfg, depuis)
    except sumup.SumUpError as e:
        raise HTTPException(502, str(e))
    except Exception as e:
        raise HTTPException(502, f"SumUp injoignable : {e}")

    res = await _enregistre(db, user, lignes, TransactionCategory.HONEY_SALE)
    cfg["last_sync_at"] = datetime.utcnow().isoformat()
    await _save_sumup(db, cfg)
    await log_action(db, user.id, "sumup_sync", "transaction", None,
                     details=f"{res.created} créée(s), {res.skipped} déjà connue(s)")
    res.detail = (
        f"{res.created} écriture(s) ajoutée(s), {res.skipped} déjà connue(s). "
        "L'API SumUp ne fournit que les encaissements : importez le relevé "
        "pour les dépenses."
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
