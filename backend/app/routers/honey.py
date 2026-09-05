"""Routes — Miellée (récoltes, pots, ventes de miel).

Règles d'isolation privé / associatif :
- Associatif : visible par tous, gérable par admin + yard_manager + treasurer
- Privé : visible UNIQUEMENT par le créateur + admin + yard_manager
- Vente privée : PAS de transaction comptable (la compta = asso uniquement)
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, or_

from app.database import get_db
from app.models.honey import HoneyHarvest, HoneyCategory, HoneyJar, HoneySale, OwnershipFilter
from app.models.treasury import Transaction, TransactionType, TransactionCategory
from app.models.user import User, RoleEnum
from app.schemas.honey import (
    SaleUpdate, HarvestLossIn, JarAdjustIn,
    HoneyCategoryCreate, HoneyCategoryOut,
    HoneyHarvestCreate, HoneyHarvestUpdate, HoneyHarvestOut,
    JarCreate, JarUpdate, JarOut,
    SaleCreate, SaleOut,
)
from app.utils.auth import get_current_user, require_roles, get_user_roles
from app.utils.audit import log_action

router = APIRouter(prefix="/api/honey", tags=["honey"])


# ─── Helpers de visibilité ────────────────────────────────────────

def _is_manager(user: User) -> bool:
    """Admin ou yard_manager."""
    roles = get_user_roles(user)
    return RoleEnum.ADMIN.value in roles or RoleEnum.YARD_MANAGER.value in roles


def _private_filter_harvests(q, user: User, filter_user_id: int = None):
    """Filtre les récoltes : asso visible par tous, privé visible par owner + managers.
    Si filter_user_id est fourni (admin only), filtre les privés de cet utilisateur."""
    if _is_manager(user):
        if filter_user_id:
            return q.where(
                or_(
                    HoneyHarvest.ownership == OwnershipFilter.ASSOCIATIVE,
                    HoneyHarvest.created_by == filter_user_id,
                )
            )
        return q  # voit tout
    # Sinon : associatif OU (privé ET créé par moi)
    return q.where(
        or_(
            HoneyHarvest.ownership == OwnershipFilter.ASSOCIATIVE,
            HoneyHarvest.created_by == user.id,
        )
    )


def _private_filter_jars(q, user: User, filter_user_id: int = None):
    """Filtre les pots : asso visible par tous, privé visible par owner + managers."""
    if _is_manager(user):
        if filter_user_id:
            return q.where(
                or_(
                    HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE,
                    HoneyJar.created_by == filter_user_id,
                )
            )
        return q
    return q.where(
        or_(
            HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE,
            HoneyJar.created_by == user.id,
        )
    )


def _private_filter_sales(q, user: User):
    """Filtre les ventes : asso visible par tous, privé visible par vendeur + managers."""
    if _is_manager(user):
        return q
    return q.where(
        or_(
            HoneySale.jar.has(HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE),
            HoneySale.sold_by == user.id,
        )
    )


# ─── Catégories de miel ───────────────────────────────────────────

@router.get("/categories", response_model=list[HoneyCategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(HoneyCategory).order_by(HoneyCategory.name))
    return result.scalars().all()


@router.post("/categories", response_model=HoneyCategoryOut, status_code=201)
async def create_category(
    body: HoneyCategoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    cat = HoneyCategory(**body.model_dump())
    db.add(cat)
    await db.flush()
    await log_action(db, user.id, "create", "honey_category", cat.id)
    return cat


@router.delete("/categories/{cat_id}", status_code=204)
async def delete_category(
    cat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    cat = await db.get(HoneyCategory, cat_id)
    if not cat:
        raise HTTPException(404, "Catégorie introuvable")
    await db.delete(cat)
    await log_action(db, user.id, "delete", "honey_category", cat_id)


# ─── Récoltes ─────────────────────────────────────────────────────

@router.get("/private-users")
async def list_private_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste les utilisateurs ayant des récoltes privées (pour le filtre admin)."""
    if not _is_manager(user):
        raise HTTPException(403, "Réservé aux responsables")
    q = (
        select(User.id, User.first_name, User.last_name)
        .join(HoneyHarvest, HoneyHarvest.created_by == User.id)
        .where(HoneyHarvest.ownership == OwnershipFilter.PRIVATE)
        .group_by(User.id, User.first_name, User.last_name)
        .order_by(User.last_name)
    )
    result = await db.execute(q)
    return [{"id": r.id, "name": f"{r.first_name or ''} {r.last_name or ''}".strip()}
            for r in result.all()]


@router.get("/", response_model=list[HoneyHarvestOut])
async def list_harvests(
    year: int = None,
    ownership: str = None,
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(HoneyHarvest).order_by(HoneyHarvest.harvest_date.desc()).limit(200)
    if year:
        q = q.where(extract("year", HoneyHarvest.harvest_date) == year)
    if ownership:
        q = q.where(HoneyHarvest.ownership == ownership)
    # user_id filter : seuls les managers/admins peuvent filtrer par user
    effective_user_id = user_id if (user_id and _is_manager(user)) else None
    # Un user simple qui demande ownership=private ne voit que ses propres données
    if not _is_manager(user) and ownership == 'private':
        q = q.where(HoneyHarvest.created_by == user.id)
    else:
        q = _private_filter_harvests(q, user, effective_user_id)
    result = await db.execute(q)
    return [_harvest_out(h) for h in result.scalars().all()]


@router.post("/", response_model=HoneyHarvestOut, status_code=201)
async def create_harvest(
    body: HoneyHarvestCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ownership = body.ownership if hasattr(body, 'ownership') and body.ownership else 'private'
    # Seuls admin / yard_manager peuvent créer des récoltes associatives
    if ownership == 'associative' and not _is_manager(user):
        raise HTTPException(403, "Seuls les responsables peuvent gérer les récoltes associatives")
    data = body.model_dump(exclude_unset=True)
    data["created_by"] = user.id
    if not data.get("harvest_date"):
        data["harvest_date"] = datetime.utcnow()
    h = HoneyHarvest(**data)
    db.add(h)
    await db.flush()
    await log_action(db, user.id, "create", "honey_harvest", h.id)
    await db.refresh(h)
    return _harvest_out(h)


@router.put("/{harvest_id}", response_model=HoneyHarvestOut)
async def update_harvest(
    harvest_id: int, body: HoneyHarvestUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    h = await db.get(HoneyHarvest, harvest_id)
    if not h:
        raise HTTPException(404, "Récolte introuvable")
    own = h.ownership.value if hasattr(h.ownership, 'value') else h.ownership
    # Privé : seul le créateur (ou manager) peut modifier
    if own == 'private' and h.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Vous ne pouvez modifier que vos propres récoltes privées")
    if own == 'associative' and not _is_manager(user):
        raise HTTPException(403, "Seuls les responsables peuvent modifier les récoltes associatives")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    await log_action(db, user.id, "update", "honey_harvest", h.id)
    return _harvest_out(h)


def _check_harvest_write(user: User, h: HoneyHarvest) -> None:
    own = h.ownership.value if hasattr(h.ownership, 'value') else h.ownership
    if own == 'private' and h.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Cette récolte ne vous appartient pas")
    if own == 'associative' and not _is_manager(user):
        raise HTTPException(403, "Seuls les responsables peuvent gérer les récoltes associatives")


@router.post("/{harvest_id}/loss", response_model=HoneyHarvestOut)
async def declare_harvest_loss(
    harvest_id: int,
    body: HarvestLossIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Déclare (ou corrige) une perte de miel sur une récolte.

    Une partie du miel récolté n'arrive jamais en pot : fond de cuve, filtre,
    maturateur renversé. Sans cette déclaration, ce miel restait indéfiniment
    au « reste à empoter » et le stock ne retombait jamais à zéro. La perte est
    conservée séparément de la quantité récoltée : le volume réellement récolté
    reste exact pour les statistiques de production.
    """
    h = await db.get(HoneyHarvest, harvest_id)
    if not h:
        raise HTTPException(404, "Récolte introuvable")
    _check_harvest_write(user, h)

    if body.kg == 0:
        raise HTTPException(400, "Indiquez une quantité différente de zéro.")

    new_loss = round((h.loss_kg or 0) + body.kg, 3)
    if new_loss < 0:
        raise HTTPException(400, "La correction dépasse les pertes déjà déclarées.")

    jarred = sum(((j.initial_quantity or j.quantity or 0) * j.jar_weight_g) / 1000
                 for j in (h.jars or []))
    if new_loss + jarred > (h.quantity_kg or 0) + 0.001:
        reste = round(max(0.0, (h.quantity_kg or 0) - jarred), 2)
        raise HTTPException(
            400,
            f"Perte supérieure au miel disponible : il reste {reste} kg à empoter "
            f"sur cette récolte.",
        )

    h.loss_kg = new_loss
    verb = "perte" if body.kg > 0 else "correction de perte"
    await log_action(db, user.id, "loss", "honey_harvest", h.id,
                     details=f"{verb} {body.kg:+g} kg — {body.reason}")
    await db.flush()
    await db.refresh(h)
    return _harvest_out(h)


@router.delete("/{harvest_id}", status_code=204)
async def delete_harvest(
    harvest_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    h = await db.get(HoneyHarvest, harvest_id)
    if not h:
        raise HTTPException(404, "Récolte introuvable")
    own = h.ownership.value if hasattr(h.ownership, 'value') else h.ownership
    # Privé : le créateur peut supprimer sa propre récolte
    if own == 'private' and h.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Vous ne pouvez supprimer que vos propres récoltes")
    if own == 'associative':
        roles = get_user_roles(user)
        if RoleEnum.ADMIN.value not in roles:
            raise HTTPException(403, "Seul l'admin peut supprimer une récolte associative")
    await db.delete(h)
    await log_action(db, user.id, "delete", "honey_harvest", harvest_id)


@router.get("/stats")
async def harvest_stats(
    year: int = None,
    ownership: str = None,
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    y = year or datetime.utcnow().year

    base_filter = [extract("year", HoneyHarvest.harvest_date) == y]
    if ownership:
        base_filter.append(HoneyHarvest.ownership == ownership)

    # ── Isolation : pour les stats, un user simple ne voit que asso + ses propres privés
    effective_user_id = user_id if (user_id and _is_manager(user)) else None
    if not _is_manager(user):
        base_filter.append(
            or_(
                HoneyHarvest.ownership == OwnershipFilter.ASSOCIATIVE,
                HoneyHarvest.created_by == user.id,
            )
        )
    elif effective_user_id:
        base_filter.append(
            or_(
                HoneyHarvest.ownership == OwnershipFilter.ASSOCIATIVE,
                HoneyHarvest.created_by == effective_user_id,
            )
        )

    total_q = select(
        func.coalesce(func.sum(HoneyHarvest.quantity_kg), 0).label("total_kg"),
        func.count(HoneyHarvest.id).label("nb_harvests"),
    ).where(*base_filter)
    total = (await db.execute(total_q)).one()

    by_cat_q = select(
        func.coalesce(HoneyCategory.name, 'Non catégorisé').label("category"),
        func.sum(HoneyHarvest.quantity_kg).label("total_kg"),
        func.count(HoneyHarvest.id).label("nb_harvests"),
    ).outerjoin(HoneyCategory, HoneyHarvest.category_id == HoneyCategory.id
    ).where(*base_filter
    ).group_by(HoneyCategory.name
    ).order_by(func.sum(HoneyHarvest.quantity_kg).desc())
    by_cat = (await db.execute(by_cat_q)).all()

    by_month_q = select(
        extract("month", HoneyHarvest.harvest_date).label("month"),
        func.sum(HoneyHarvest.quantity_kg).label("total_kg"),
    ).where(*base_filter
    ).group_by(extract("month", HoneyHarvest.harvest_date)
    ).order_by(extract("month", HoneyHarvest.harvest_date))
    by_month = (await db.execute(by_month_q)).all()

    # Stats par ownership (avec le même filtre de visibilité)
    by_own_q = select(
        HoneyHarvest.ownership.label("ownership"),
        func.sum(HoneyHarvest.quantity_kg).label("total_kg"),
        func.count(HoneyHarvest.id).label("nb_harvests"),
    ).where(*base_filter
    ).group_by(HoneyHarvest.ownership)
    by_own = (await db.execute(by_own_q)).all()

    return {
        "year": y,
        "total_kg": float(total.total_kg),
        "nb_harvests": total.nb_harvests,
        "by_category": [
            {"category": r.category, "total_kg": float(r.total_kg), "nb_harvests": r.nb_harvests}
            for r in by_cat
        ],
        "by_month": [
            {"month": int(r.month), "total_kg": float(r.total_kg)}
            for r in by_month
        ],
        "by_ownership": [
            {"ownership": r.ownership.value if hasattr(r.ownership, 'value') else r.ownership,
             "total_kg": float(r.total_kg), "nb_harvests": r.nb_harvests}
            for r in by_own
        ],
    }


# ─── Pots (mise en pot) ──────────────────────────────────────────

@router.get("/jars", response_model=list[JarOut])
async def list_jars(
    ownership: str = None,
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(HoneyJar).order_by(HoneyJar.created_at.desc())
    if ownership:
        q = q.where(HoneyJar.ownership == ownership)
    effective_user_id = user_id if (user_id and _is_manager(user)) else None
    if not _is_manager(user) and ownership == 'private':
        q = q.where(HoneyJar.created_by == user.id)
    else:
        q = _private_filter_jars(q, user, effective_user_id)
    result = await db.execute(q)
    return [_jar_out(j) for j in result.scalars().all()]


@router.post("/jars", response_model=JarOut, status_code=201)
async def create_jar(
    body: JarCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    harvest = await db.get(HoneyHarvest, body.harvest_id)
    if not harvest:
        raise HTTPException(404, "Récolte introuvable")
    harvest_own = harvest.ownership.value if hasattr(harvest.ownership, 'value') else harvest.ownership
    # Vérifier que l'utilisateur a le droit de toucher à cette récolte
    if harvest_own == 'private' and harvest.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Cette récolte ne vous appartient pas")
    ownership = body.ownership or harvest_own
    if ownership == 'associative' and not _is_manager(user):
        raise HTTPException(403, "Seuls les responsables peuvent gérer les pots associatifs")

    # Un lot = une récolte + un format. Remettre en pot la même récolte au même
    # format alimente la ligne existante plutôt que d'en créer une seconde :
    # sans cela, le même lot apparaissait deux fois à la vente.
    existing = (await db.execute(
        select(HoneyJar).where(
            HoneyJar.harvest_id == body.harvest_id,
            HoneyJar.jar_weight_g == body.jar_weight_g,
            HoneyJar.ownership == ownership,
        ).limit(1)
    )).scalar_one_or_none()

    if existing:
        existing.quantity += body.quantity
        existing.initial_quantity += body.quantity
        if body.unit_price is not None:
            existing.unit_price = body.unit_price
        await log_action(db, user.id, "update", "honey_jar", existing.id,
                         details=f"+{body.quantity} pot(s) de {body.jar_weight_g}g")
        await db.flush()
        await db.refresh(existing)
        return _jar_out(existing)

    jar = HoneyJar(
        harvest_id=body.harvest_id,
        category_id=body.category_id or harvest.category_id,
        ownership=ownership,
        jar_weight_g=body.jar_weight_g,
        quantity=body.quantity,
        initial_quantity=body.quantity,
        unit_price=body.unit_price,
        created_by=user.id,
    )
    db.add(jar)
    await db.flush()
    await log_action(db, user.id, "create", "honey_jar", jar.id)
    await db.refresh(jar)
    return _jar_out(jar)


@router.put("/jars/{jar_id}", response_model=JarOut)
async def update_jar(
    jar_id: int, body: JarUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    jar = await db.get(HoneyJar, jar_id)
    if not jar:
        raise HTTPException(404, "Pot introuvable")
    own = jar.ownership.value if hasattr(jar.ownership, 'value') else jar.ownership
    if own == 'private' and jar.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Ce pot ne vous appartient pas")
    if own == 'associative' and not _is_manager(user):
        raise HTTPException(403, "Seuls les responsables peuvent modifier les pots associatifs")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(jar, k, v)
    await log_action(db, user.id, "update", "honey_jar", jar.id)
    return _jar_out(jar)


@router.get("/jars/stock")
async def jar_stock_summary(
    ownership: str = None,
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stock de pots détaillé **par lot**.

    Un lot = une récolte + un format de pot. Les mises en pot successives
    d'une même récolte au même format se cumulent, mais deux récoltes
    différentes restent séparées : c'est ce qui permet de tracer l'origine
    d'un pot vendu.
    """
    q = (
        select(
            HoneyJar.harvest_id,
            HoneyJar.jar_weight_g,
            HoneyJar.ownership,
            func.sum(HoneyJar.quantity).label("stock"),
            func.sum(HoneyJar.initial_quantity).label("initial"),
            func.sum(HoneyJar.lost_quantity).label("lost"),
            func.max(HoneyJar.unit_price).label("unit_price"),
            HoneyHarvest.harvest_date,
            HoneyHarvest.created_by,
            func.coalesce(HoneyCategory.name, "Non catégorisé").label("category"),
        )
        .join(HoneyHarvest, HoneyJar.harvest_id == HoneyHarvest.id)
        .outerjoin(HoneyCategory, HoneyJar.category_id == HoneyCategory.id)
    )
    if ownership:
        q = q.where(HoneyJar.ownership == ownership)

    # ── Isolation privé : un adhérent ne voit que l'associatif et ses lots ──
    effective_user_id = user_id if (user_id and _is_manager(user)) else None
    if not _is_manager(user):
        q = q.where(or_(
            HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE,
            HoneyJar.created_by == user.id,
        ))
    elif effective_user_id:
        q = q.where(or_(
            HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE,
            HoneyJar.created_by == effective_user_id,
        ))

    q = q.group_by(
        HoneyJar.harvest_id, HoneyJar.jar_weight_g, HoneyJar.ownership,
        HoneyHarvest.harvest_date, HoneyHarvest.created_by, HoneyCategory.name,
    ).order_by(HoneyHarvest.harvest_date.desc(), HoneyJar.jar_weight_g.desc())

    rows = (await db.execute(q)).all()

    # Nom du propriétaire des lots privés, pour les responsables.
    owner_names = {}
    if _is_manager(user):
        ids = {r.created_by for r in rows if r.created_by}
        if ids:
            res = await db.execute(select(User).where(User.id.in_(ids)))
            owner_names = {u.id: f"{u.first_name} {u.last_name}".strip() for u in res.scalars().all()}

    out = []
    for r in rows:
        own = r.ownership.value if hasattr(r.ownership, "value") else r.ownership
        initial = r.initial or 0
        stock = r.stock or 0
        lost = r.lost or 0
        out.append({
            "harvest_id": r.harvest_id,
            # Référence de lot lisible : date de récolte + identifiant.
            "lot": f"L{r.harvest_date:%y%m%d}-{r.harvest_id}" if r.harvest_date else f"L{r.harvest_id}",
            "harvest_date": r.harvest_date,
            "category": r.category,
            "jar_weight_g": r.jar_weight_g,
            "ownership": own,
            "stock": stock,
            "initial": initial,
            "lost": lost,
            # Un pot cassé sort du stock sans avoir été vendu : sans le
            # retrancher, la casse était comptabilisée comme une vente.
            "sold": max(0, initial - stock - lost),
            "unit_price": r.unit_price,
            "owner_name": owner_names.get(r.created_by) if own == "private" else None,
        })
    return out


@router.post("/jars/adjust")
async def adjust_jar_stock(
    body: JarAdjustIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Corrige à la main le nombre de pots en stock d'un lot.

    Casse, don, écart d'inventaire : l'écart est enregistré comme une perte,
    jamais comme une vente — sinon le chiffre d'affaires du lot devenait faux.
    """
    if body.new_stock < 0:
        raise HTTPException(400, "Le stock ne peut pas être négatif.")

    harvest = await db.get(HoneyHarvest, body.harvest_id)
    if not harvest:
        raise HTTPException(404, "Récolte introuvable")

    rows = (await db.execute(
        select(HoneyJar).where(
            HoneyJar.harvest_id == body.harvest_id,
            HoneyJar.jar_weight_g == body.jar_weight_g,
            HoneyJar.ownership == body.ownership,
        ).order_by(HoneyJar.id)
    )).scalars().all()
    if not rows:
        raise HTTPException(404, "Lot introuvable")

    first = rows[0]
    own = first.ownership.value if hasattr(first.ownership, 'value') else first.ownership
    if own == 'private' and first.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Ce lot ne vous appartient pas")
    if own == 'associative' and not _is_manager(user):
        raise HTTPException(403, "Seuls les responsables peuvent gérer les pots associatifs")

    current = sum(r.quantity or 0 for r in rows)
    delta = body.new_stock - current
    if delta == 0:
        raise HTTPException(400, "Ce lot est déjà à ce nombre de pots.")

    if delta < 0:
        # Retrait : on puise dans les lignes du lot, et on compte la perte.
        to_remove = -delta
        for r in rows:
            if to_remove <= 0:
                break
            take = min(r.quantity or 0, to_remove)
            r.quantity -= take
            r.lost_quantity = (r.lost_quantity or 0) + take
            to_remove -= take
    else:
        # Ajout : on annule d'abord des pertes déjà déclarées (correction d'une
        # saisie), et seulement ensuite on remet des pots en stock.
        to_add = delta
        for r in rows:
            if to_add <= 0:
                break
            back = min(r.lost_quantity or 0, to_add)
            if back:
                r.lost_quantity -= back
                r.quantity += back
                to_add -= back
        if to_add:
            first.quantity += to_add
            first.initial_quantity = (first.initial_quantity or 0) + to_add

    await log_action(db, user.id, "adjust", "honey_jar", first.id,
                     details=f"stock {current} → {body.new_stock} pots "
                             f"de {body.jar_weight_g} g — {body.reason}")
    await db.flush()
    return {
        "harvest_id": body.harvest_id,
        "jar_weight_g": body.jar_weight_g,
        "ownership": body.ownership,
        "stock": body.new_stock,
        "delta": delta,
        "detail": (f"{-delta} pot(s) retiré(s) du stock" if delta < 0
                   else f"{delta} pot(s) remis en stock"),
    }


# ─── Ventes ───────────────────────────────────────────────────────

@router.get("/sales", response_model=list[SaleOut])
async def list_sales(
    ownership: str = None,
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(HoneySale).order_by(HoneySale.sold_at.desc()).limit(200)
    if ownership:
        q = q.join(HoneyJar, HoneySale.jar_id == HoneyJar.id).where(HoneyJar.ownership == ownership)
    # ── Isolation privé ──
    effective_user_id = user_id if (user_id and _is_manager(user)) else None
    if not _is_manager(user):
        if not ownership:
            q = q.join(HoneyJar, HoneySale.jar_id == HoneyJar.id, isouter=True)
        q = q.where(
            or_(
                HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE,
                HoneySale.sold_by == user.id,
            )
        )
    elif effective_user_id:
        if not ownership:
            q = q.join(HoneyJar, HoneySale.jar_id == HoneyJar.id, isouter=True)
        q = q.where(
            or_(
                HoneyJar.ownership == OwnershipFilter.ASSOCIATIVE,
                HoneySale.sold_by == effective_user_id,
            )
        )
    result = await db.execute(q)
    return [_sale_out(s) for s in result.scalars().all()]


@router.post("/sales", response_model=SaleOut, status_code=201)
async def create_sale(
    body: SaleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    jar = await db.get(HoneyJar, body.jar_id)
    if not jar:
        raise HTTPException(404, "Pot introuvable")
    own = jar.ownership.value if hasattr(jar.ownership, 'value') else jar.ownership

    # Vérifier les droits
    if own == 'private' and jar.created_by != user.id and not _is_manager(user):
        raise HTTPException(403, "Ce pot ne vous appartient pas")
    if own == 'associative':
        roles = get_user_roles(user)
        if RoleEnum.ADMIN.value not in roles and RoleEnum.TREASURER.value not in roles and RoleEnum.YARD_MANAGER.value not in roles:
            raise HTTPException(403, "Seuls les responsables peuvent vendre les pots associatifs")

    if jar.quantity < body.quantity:
        raise HTTPException(400, f"Stock insuffisant ({jar.quantity} disponibles)")

    price = body.unit_price if body.unit_price is not None else jar.unit_price
    if not price:
        raise HTTPException(400, "Prix unitaire requis")

    total = round(price * body.quantity, 2)

    # Décrémenter le stock
    jar.quantity -= body.quantity

    # ── Compta : UNIQUEMENT pour les ventes associatives ──
    tx_id = None
    if own == 'associative':
        tx = Transaction(
            transaction_type=TransactionType.INCOME,
            category=TransactionCategory.HONEY_SALE,
            amount=total,
            description=f"Vente asso {body.quantity}x pot {jar.jar_weight_g}g"
                        + (f" — {body.buyer}" if body.buyer else ""),
            supplier=body.buyer,
            date=datetime.utcnow(),
            created_by=user.id,
        )
        db.add(tx)
        await db.flush()
        tx_id = tx.id

    sale = HoneySale(
        jar_id=body.jar_id,
        quantity=body.quantity,
        unit_price=price,
        total_amount=total,
        buyer=body.buyer,
        transaction_id=tx_id,
        sold_by=user.id,
    )
    db.add(sale)
    await db.flush()
    await log_action(db, user.id, "create", "honey_sale", sale.id,
                     details=f"[{own}] {body.quantity}x {jar.jar_weight_g}g = {total}€")
    await db.refresh(sale)
    return _sale_out(sale)


async def _check_sale_access(db, sale: HoneySale, user: User) -> tuple[HoneyJar, str]:
    """Vérifie que l'utilisateur peut toucher à cette vente. Renvoie (pot, ownership)."""
    jar = await db.get(HoneyJar, sale.jar_id)
    if not jar:
        raise HTTPException(404, "Pot introuvable")
    own = jar.ownership.value if hasattr(jar.ownership, 'value') else jar.ownership
    if own == 'private':
        # Privé : le vendeur, le propriétaire du pot, ou un responsable.
        if sale.sold_by != user.id and jar.created_by != user.id and not _is_manager(user):
            raise HTTPException(403, "Cette vente ne vous appartient pas")
    else:
        roles = get_user_roles(user)
        if not any(r in roles for r in (RoleEnum.ADMIN.value, RoleEnum.TREASURER.value,
                                        RoleEnum.YARD_MANAGER.value)):
            raise HTTPException(403, "Seuls les responsables peuvent modifier les ventes associatives")
    return jar, own


@router.put("/sales/{sale_id}", response_model=SaleOut)
async def update_sale(
    sale_id: int, body: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Corrige une vente : le stock du pot et l'écriture comptable liée suivent."""
    sale = await db.get(HoneySale, sale_id)
    if not sale:
        raise HTTPException(404, "Vente introuvable")
    jar, own = await _check_sale_access(db, sale, user)

    new_qty = sale.quantity if body.quantity is None else body.quantity
    if new_qty <= 0:
        raise HTTPException(400, "La quantité vendue doit être positive")

    # Le stock doit absorber l'écart : rendre les pots repris, retirer les
    # pots supplémentaires — sans jamais passer sous zéro.
    delta = new_qty - sale.quantity
    if delta > 0 and jar.quantity < delta:
        raise HTTPException(400, f"Stock insuffisant ({jar.quantity} disponible(s) en plus)")
    jar.quantity -= delta

    price = sale.unit_price if body.unit_price is None else body.unit_price
    if not price or price <= 0:
        raise HTTPException(400, "Prix unitaire requis")

    sale.quantity = new_qty
    sale.unit_price = price
    sale.total_amount = round(price * new_qty, 2)
    if body.buyer is not None:
        sale.buyer = body.buyer or None

    # Répercuter sur l'écriture comptable (ventes associatives uniquement).
    if sale.transaction_id:
        tx = await db.get(Transaction, sale.transaction_id)
        if tx:
            tx.amount = sale.total_amount
            tx.description = (f"Vente asso {sale.quantity}x pot {jar.jar_weight_g}g"
                              + (f" — {sale.buyer}" if sale.buyer else ""))
            tx.supplier = sale.buyer

    await log_action(db, user.id, "update", "honey_sale", sale.id,
                     details=f"[{own}] {sale.quantity}x {jar.jar_weight_g}g = {sale.total_amount}€")
    await db.flush()
    return _sale_out(sale)


@router.delete("/sales/{sale_id}", status_code=204)
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Annule une vente : les pots retournent en stock et l'écriture est supprimée."""
    sale = await db.get(HoneySale, sale_id)
    if not sale:
        raise HTTPException(404, "Vente introuvable")
    jar, own = await _check_sale_access(db, sale, user)

    jar.quantity += sale.quantity
    if sale.transaction_id:
        tx = await db.get(Transaction, sale.transaction_id)
        if tx:
            await db.delete(tx)

    qty, weight = sale.quantity, jar.jar_weight_g
    await db.delete(sale)
    await log_action(db, user.id, "delete", "honey_sale", sale_id,
                     details=f"[{own}] {qty}x {weight}g remis en stock")


# ─── Helpers ──────────────────────────────────────────────────────

def _harvest_out(h: HoneyHarvest) -> HoneyHarvestOut:
    return HoneyHarvestOut(
        id=h.id,
        apiary_id=h.apiary_id,
        hive_id=h.hive_id,
        category_id=h.category_id,
        ownership=h.ownership.value if hasattr(h.ownership, 'value') else h.ownership,
        harvest_date=h.harvest_date,
        quantity_kg=h.quantity_kg,
        loss_kg=h.loss_kg or 0,
        nb_frames=h.nb_frames,
        nb_supers=h.nb_supers,
        notes=h.notes,
        created_by=h.created_by,
        created_at=h.created_at,
        category_name=h.category.name if h.category else None,
        apiary_name=h.apiary.name if h.apiary else None,
        hive_name=(h.hive.name or h.hive.number or h.hive.napi_number
                   or f"Ruche #{h.hive.id}") if h.hive else None,
        jars=[{"id": j.id, "jar_weight_g": j.jar_weight_g, "quantity": j.quantity,
               "initial_quantity": j.initial_quantity,
               "lost_quantity": j.lost_quantity or 0, "unit_price": j.unit_price}
              for j in (h.jars or [])],
    )


def _jar_out(j: HoneyJar) -> JarOut:
    return JarOut(
        id=j.id,
        harvest_id=j.harvest_id,
        category_id=j.category_id,
        ownership=j.ownership.value if hasattr(j.ownership, 'value') else j.ownership,
        jar_weight_g=j.jar_weight_g,
        quantity=j.quantity,
        initial_quantity=j.initial_quantity,
        lost_quantity=j.lost_quantity or 0,
        unit_price=j.unit_price,
        category_name=j.category.name if j.category else None,
        lot=_lot_ref(j.harvest),
        harvest_date=j.harvest.harvest_date if j.harvest else None,
        created_at=j.created_at,
    )


def _lot_ref(h) -> str | None:
    """Référence de lot lisible : date de récolte + identifiant de récolte."""
    if not h:
        return None
    return f"L{h.harvest_date:%y%m%d}-{h.id}" if h.harvest_date else f"L{h.id}"


def _sale_out(s: HoneySale) -> SaleOut:
    jar = s.jar
    return SaleOut(
        id=s.id,
        jar_id=s.jar_id,
        quantity=s.quantity,
        unit_price=s.unit_price,
        total_amount=s.total_amount,
        buyer=s.buyer,
        transaction_id=s.transaction_id,
        sold_at=s.sold_at,
        sold_by=s.sold_by,
        jar_weight_g=jar.jar_weight_g if jar else None,
        category_name=jar.category.name if jar and jar.category else None,
        ownership=jar.ownership.value if jar and hasattr(jar.ownership, 'value') else None,
    )
