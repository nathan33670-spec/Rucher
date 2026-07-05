"""Routes — Documentation.

Lecture PUBLIQUE (sans authentification) ; création/édition réservée aux admins.
Permet aux administrateurs de créer facilement des pages de documentation.
"""

import re
import unicodedata
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.doc import DocPage
from app.models.user import User, RoleEnum
from app.schemas.doc import DocPageCreate, DocPageUpdate, DocPageOut, DocPageListItem
from app.utils.auth import require_roles
from app.utils.audit import log_action

router = APIRouter(prefix="/api/docs", tags=["docs"])


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "page"


# ─── Lecture publique ──────────────────────────────────────────────
@router.get("/", response_model=list[DocPageListItem])
async def list_docs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DocPage).where(DocPage.is_published == True)  # noqa: E712
        .order_by(DocPage.category, DocPage.sort_order, DocPage.title)
    )
    return list(result.scalars().all())


@router.get("/{slug}", response_model=DocPageOut)
async def get_doc(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocPage).where(DocPage.slug == slug))
    page = result.scalar_one_or_none()
    if not page or not page.is_published:
        raise HTTPException(status_code=404, detail="Page introuvable")
    return page


# ─── Écriture réservée aux admins ──────────────────────────────────
@router.post("/", response_model=DocPageOut, status_code=201)
async def create_doc(
    body: DocPageCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    slug = slugify(body.slug or body.title)
    # Unicité du slug
    exists = await db.execute(select(DocPage).where(DocPage.slug == slug))
    if exists.scalar_one_or_none():
        slug = f"{slug}-{int(__import__('time').time())}"
    page = DocPage(
        slug=slug, title=body.title, category=body.category,
        content=body.content, is_published=body.is_published,
        sort_order=body.sort_order, author_id=current.id,
    )
    db.add(page)
    await db.flush()
    await log_action(db, current.id, "create", "doc_page", page.id)
    await db.refresh(page)
    return page


@router.put("/{page_id}", response_model=DocPageOut)
async def update_doc(
    page_id: int,
    body: DocPageUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(DocPage).where(DocPage.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page introuvable")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(page, field, value)
    await log_action(db, current.id, "update", "doc_page", page.id)
    await db.flush()
    await db.refresh(page)
    return page


@router.delete("/{page_id}")
async def delete_doc(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(DocPage).where(DocPage.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page introuvable")
    await db.delete(page)
    await log_action(db, current.id, "delete", "doc_page", page_id)
    return {"detail": "Page supprimée"}
