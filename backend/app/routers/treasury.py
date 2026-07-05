"""Routes — Trésorerie."""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.treasury import Transaction, Invoice, TransactionType
from app.models.user import User, RoleEnum
from app.schemas.treasury import TransactionCreate, TransactionUpdate, TransactionOut
from app.utils.auth import get_current_user, require_roles
from app.utils.audit import log_action
from app.config import get_settings

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


@router.get("/", response_model=list[TransactionOut])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
    return {"id": invoice.id, "filename": invoice.filename}


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
        created_by=t.created_by,
        invoices=[{"id": inv.id, "filename": inv.filename} for inv in t.invoices],
        created_at=t.created_at,
    )
