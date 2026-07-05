"""Routes — Inventaire."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.inventory import InventoryItem, InventoryMovement, MovementType
from app.models.user import User, RoleEnum
from app.schemas.inventory import ItemCreate, ItemUpdate, ItemOut, ItemMove, MovementCreate, MovementOut
from app.utils.auth import get_current_user, require_roles
from app.utils.audit import log_action

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/", response_model=list[ItemOut])
async def list_items(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(InventoryItem).order_by(InventoryItem.name))
    return result.scalars().all()


@router.post("/", response_model=ItemOut, status_code=201)
async def create_item(
    body: ItemCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER, RoleEnum.TREASURER)),
):
    item = InventoryItem(**body.model_dump())
    db.add(item)
    await db.flush()
    await log_action(db, user.id, "create", "inventory_item", item.id)
    return item


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int, body: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER, RoleEnum.TREASURER)),
):
    item = await db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await log_action(db, user.id, "update", "inventory_item", item.id)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    item = await db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")
    await db.delete(item)
    await log_action(db, user.id, "delete", "inventory_item", item_id)


@router.post("/movements", response_model=MovementOut, status_code=201)
async def create_movement(
    body: MovementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER, RoleEnum.TREASURER)),
):
    item = await db.get(InventoryItem, body.item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")

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
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/alerts")
async def stock_alerts(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Retourne les articles dont le stock est sous le seuil d'alerte."""
    result = await db.execute(
        select(InventoryItem).where(
            InventoryItem.alert_threshold.isnot(None),
            InventoryItem.quantity <= InventoryItem.alert_threshold,
        )
    )
    items = result.scalars().all()
    return [{"id": i.id, "name": i.name, "quantity": i.quantity, "threshold": i.alert_threshold} for i in items]


@router.put("/{item_id}/move")
async def move_item(
    item_id: int,
    body: ItemMove,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    """Déplace tout ou partie d'un article vers un autre point de stockage.

    - Quantité absente ou égale au stock → déplacement total (changement d'emplacement).
    - Quantité partielle → l'article est scindé : le stock restant demeure à l'origine
      et la quantité déplacée rejoint (ou crée) un article identique à destination.
    """
    item = await db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "Article introuvable")

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
        )
        db.add(target)
        await db.flush()

    await log_action(db, user.id, "move", "inventory_item", item.id,
                     details=f"{old_location} → {new_location} (partiel : {move_qty} {item.unit})")
    return {"id": target.id, "name": target.name, "location": target.location,
            "quantity": target.quantity, "source_remaining": item.quantity, "split": True}


@router.get("/locations/summary")
async def locations_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Résumé par point de stockage : nombre d'articles, quantité totale, valeur."""
    result = await db.execute(
        select(
            func.coalesce(InventoryItem.location, 'Non assigné').label('location'),
            func.count(InventoryItem.id).label('item_count'),
            func.sum(InventoryItem.quantity).label('total_qty'),
            func.sum(InventoryItem.quantity * InventoryItem.unit_price).label('total_value'),
        ).group_by(InventoryItem.location).order_by('location')
    )
    return [
        {"location": r.location, "item_count": r.item_count,
         "total_qty": r.total_qty or 0, "total_value": float(r.total_value or 0)}
        for r in result.all()
    ]
