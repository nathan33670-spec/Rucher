"""Routes — Inventaire."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.inventory import InventoryItem, InventoryMovement, MovementType
from app.models.user import User, RoleEnum
from app.schemas.inventory import ItemCreate, ItemUpdate, ItemOut, ItemMove, MovementCreate, MovementOut
from app.utils.auth import get_current_user, require_roles, get_user_roles
from app.utils.audit import log_action
from app.utils.push import notify

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _is_stock_manager(user: User) -> bool:
    """Gère le matériel de l'association (admin, responsable rucher, trésorier)."""
    roles = get_user_roles(user)
    return any(r in roles for r in (
        RoleEnum.ADMIN.value, RoleEnum.YARD_MANAGER.value, RoleEnum.TREASURER.value,
    ))


def _visible_filter(q, user: User):
    """Le matériel personnel d'un adhérent n'appartient qu'à lui.

    Le matériel de l'association (``owner_user_id`` nul) reste visible de tous ;
    celui d'un adhérent n'est visible que par lui-même et par les responsables —
    même règle que pour le miel privé.
    """
    if _is_stock_manager(user):
        return q
    return q.where(
        or_(InventoryItem.owner_user_id.is_(None),
            InventoryItem.owner_user_id == user.id)
    )


def _check_can_edit(user: User, item: InventoryItem) -> None:
    """Un adhérent gère son propre matériel ; l'association, ses responsables."""
    if _is_stock_manager(user):
        return
    if item.owner_user_id and item.owner_user_id == user.id:
        return
    if item.owner_user_id is None:
        raise HTTPException(403, "Le matériel de l'association est géré par les responsables")
    raise HTTPException(403, "Cet article appartient à un autre adhérent")


async def _owner_names(db: AsyncSession, items) -> dict:
    ids = {i.owner_user_id for i in items if i.owner_user_id}
    if not ids:
        return {}
    res = await db.execute(select(User).where(User.id.in_(ids)))
    return {u.id: f"{u.first_name} {u.last_name}".strip() for u in res.scalars().all()}


def _item_out(item: InventoryItem, names: dict) -> ItemOut:
    data = ItemOut.model_validate(item)
    data.owner_name = names.get(item.owner_user_id) if item.owner_user_id else None
    return data


@router.get("/", response_model=list[ItemOut])
async def list_items(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(_visible_filter(select(InventoryItem), user).order_by(InventoryItem.name))
    items = list(result.scalars().all())
    names = await _owner_names(db, items)
    return [_item_out(i, names) for i in items]


@router.post("/", response_model=ItemOut, status_code=201)
async def create_item(
    body: ItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Chacun peut déclarer son propre matériel ; celui de l'association reste
    réservé aux responsables."""
    data = body.model_dump()
    if not _is_stock_manager(user):
        # Un adhérent ne peut créer que du matériel lui appartenant : ni celui
        # de l'association, ni celui d'un autre adhérent.
        if data.get("owner_user_id") not in (None, user.id):
            raise HTTPException(403, "Vous ne pouvez déclarer que votre propre matériel")
        data["owner_user_id"] = user.id
    item = InventoryItem(**data)
    db.add(item)
    await db.flush()
    await log_action(db, user.id, "create", "inventory_item", item.id)
    return _item_out(item, await _owner_names(db, [item]))


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int, body: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")
    _check_can_edit(user, item)
    changes = body.model_dump(exclude_unset=True)
    if not _is_stock_manager(user) and "owner_user_id" in changes:
        # Sinon un adhérent pourrait « donner » son matériel à l'association
        # ou à quelqu'un d'autre, et en perdre la maîtrise.
        if changes["owner_user_id"] != user.id:
            raise HTTPException(403, "Vous ne pouvez pas changer le propriétaire de cet article")
    for k, v in changes.items():
        setattr(item, k, v)
    await log_action(db, user.id, "update", "inventory_item", item.id)
    await db.flush()
    return _item_out(item, await _owner_names(db, [item]))


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")
    # Le matériel de l'association reste supprimable par le seul administrateur ;
    # chacun dispose en revanche du sien.
    if item.owner_user_id is None:
        if RoleEnum.ADMIN.value not in get_user_roles(user):
            raise HTTPException(403, "Seul l'administrateur peut supprimer du matériel de l'association")
    else:
        _check_can_edit(user, item)
    await db.delete(item)
    await log_action(db, user.id, "delete", "inventory_item", item_id)


@router.post("/movements", response_model=MovementOut, status_code=201)
async def create_movement(
    body: MovementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = await db.get(InventoryItem, body.item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")
    _check_can_edit(user, item)
    if body.quantity <= 0:
        raise HTTPException(400, "La quantité d'un mouvement doit être positive")

    if body.movement_type == MovementType.IN:
        item.quantity += body.quantity
    else:
        if item.quantity < body.quantity:
            raise HTTPException(400, "Stock insuffisant")
        item.quantity -= body.quantity

    mvt = InventoryMovement(
        item_id=body.item_id,
        movement_type=body.movement_type,
        quantity=body.quantity,
        reason=body.reason,
        hive_id=body.hive_id,
        transaction_id=body.transaction_id,
        performed_by=user.id,
    )
    db.add(mvt)
    await db.flush()
    await log_action(db, user.id, "create", "inventory_movement", mvt.id)

    verb = "Entrée" if body.movement_type == MovementType.IN else "Sortie"
    # Le matériel personnel ne concerne que son propriétaire : inutile d'alerter
    # toute l'association à chaque mouvement.
    if item.owner_user_id is None:
        notify("inventory", "📦 Mouvement de matériel",
               f"{verb} : {body.quantity} {item.unit} — {item.name}",
               "/app/inventory", exclude_user_id=user.id)
    return mvt


@router.get("/movements", response_model=list[MovementOut])
async def list_movements(
    item_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(InventoryMovement).order_by(InventoryMovement.performed_at.desc()).limit(100)
    if item_id:
        q = q.where(InventoryMovement.item_id == item_id)
    if not _is_stock_manager(user):
        visible = _visible_filter(select(InventoryItem.id), user)
        q = q.where(InventoryMovement.item_id.in_(visible))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/alerts")
async def stock_alerts(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Retourne les articles dont le stock est sous le seuil d'alerte."""
    result = await db.execute(
        _visible_filter(
            select(InventoryItem).where(
                InventoryItem.alert_threshold.isnot(None),
                InventoryItem.quantity <= InventoryItem.alert_threshold,
            ),
            user,
        )
    )
    items = result.scalars().all()
    return [{"id": i.id, "name": i.name, "quantity": i.quantity, "threshold": i.alert_threshold} for i in items]


@router.put("/{item_id}/move")
async def move_item(
    item_id: int,
    body: ItemMove,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Déplace tout ou partie d'un article vers un autre point de stockage.

    - Quantité absente ou égale au stock → déplacement total (changement d'emplacement).
    - Quantité partielle → l'article est scindé : le stock restant demeure à l'origine
      et la quantité déplacée rejoint (ou crée) un article identique à destination.
    """
    item = await db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")
    _check_can_edit(user, item)

    new_location = (body.new_location or "").strip() or None
    old_location = item.location

    if new_location == old_location:
        raise HTTPException(400, "L'article est déjà à cet emplacement")

    move_qty = item.quantity if body.quantity is None else body.quantity
    if move_qty <= 0:
        raise HTTPException(400, "La quantité à déplacer doit être positive")
    if move_qty > item.quantity:
        raise HTTPException(400, "Quantité supérieure au stock disponible")

    # Recherche d'un article identique déjà présent à destination (pour fusion)
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id != item.id,
            InventoryItem.name == item.name,
            InventoryItem.unit == item.unit,
            func.coalesce(InventoryItem.category, "") == (item.category or ""),
            func.coalesce(InventoryItem.location, "") == (new_location or ""),
            # Un article personnel ne doit jamais fusionner avec celui d'un
            # autre adhérent, ni avec le stock de l'association.
            func.coalesce(InventoryItem.owner_user_id, 0) == (item.owner_user_id or 0),
        )
    )
    dest = result.scalars().first()
    total = move_qty == item.quantity
    source_id = item.id
    src_unit = item.unit

    # ─── Déplacement total ───
    if total:
        if dest:
            # Fusion avec l'article existant à destination ; l'article source est supprimé
            dest.quantity += move_qty
            await db.delete(item)
            target = dest
        else:
            # Simple changement d'emplacement
            item.location = new_location
            target = item
        await log_action(db, user.id, "move", "inventory_item", source_id,
                         details=f"{old_location} → {new_location} (tout : {move_qty} {src_unit})")
        notify("inventory", "📦 Déplacement de matériel",
               f"{target.name} → {new_location or 'Non assigné'}", "/app/inventory",
               exclude_user_id=user.id)
        return {"id": target.id, "name": target.name, "location": target.location,
                "quantity": target.quantity, "split": False}

    # ─── Déplacement partiel : scission de l'article ───
    item.quantity -= move_qty
    if dest:
        dest.quantity += move_qty
        target = dest
    else:
        target = InventoryItem(
            name=item.name,
            category=item.category,
            description=item.description,
            location=new_location,
            quantity=move_qty,
            unit=item.unit,
            alert_threshold=item.alert_threshold,
            unit_price=item.unit_price,
            owner_user_id=item.owner_user_id,
        )
        db.add(target)
        await db.flush()

    await log_action(db, user.id, "move", "inventory_item", item.id,
                     details=f"{old_location} → {new_location} (partiel : {move_qty} {item.unit})")
    notify("inventory", "📦 Déplacement de matériel",
           f"{move_qty} {item.unit} de {item.name} → {new_location or 'Non assigné'}", "/app/inventory",
           exclude_user_id=user.id)
    return {"id": target.id, "name": target.name, "location": target.location,
            "quantity": target.quantity, "source_remaining": item.quantity, "split": True}


@router.get("/locations/summary")
async def locations_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Résumé par point de stockage : nombre d'articles, quantité totale, valeur."""
    result = await db.execute(
        _visible_filter(select(
            func.coalesce(InventoryItem.location, 'Non assigné').label('location'),
            func.count(InventoryItem.id).label('item_count'),
            func.sum(InventoryItem.quantity).label('total_qty'),
            func.sum(InventoryItem.quantity * InventoryItem.unit_price).label('total_value'),
        ), user).group_by(InventoryItem.location).order_by('location')
    )
    return [
        {"location": r.location, "item_count": r.item_count,
         "total_qty": r.total_qty or 0, "total_value": float(r.total_value or 0)}
        for r in result.all()
    ]
