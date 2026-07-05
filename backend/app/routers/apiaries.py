"""Routes — Ruchers et Ruches."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.apiary import Apiary, Hive, hive_managers
from app.models.visit import Visit
from app.models.user import User, RoleEnum
from app.schemas.apiary import ApiaryCreate, ApiaryUpdate, ApiaryOut, HiveCreate, HiveUpdate, HiveOut
from app.utils.auth import get_current_user, require_roles, get_user_roles
from app.utils.audit import log_action
from app.config import get_settings
import os, uuid

router = APIRouter(prefix="/api/apiaries", tags=["apiaries"])


# ─── Ruchers ────────────────────────────────────────────

@router.get("/", response_model=list[ApiaryOut])
async def list_apiaries(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Apiary).order_by(Apiary.name))
    apiaries = result.scalars().all()
    out = []
    for a in apiaries:
        data = ApiaryOut.model_validate(a)
        data.hives_count = len(a.hives) if a.hives else 0
        out.append(data)
    return out


@router.post("/", response_model=ApiaryOut, status_code=201)
async def create_apiary(
    body: ApiaryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    apiary = Apiary(**body.model_dump())
    db.add(apiary)
    await db.flush()
    await log_action(db, user.id, "create", "apiary", apiary.id)
    return apiary


@router.put("/{apiary_id}", response_model=ApiaryOut)
async def update_apiary(
    apiary_id: int, body: ApiaryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    result = await db.execute(select(Apiary).where(Apiary.id == apiary_id))
    apiary = result.scalar_one_or_none()
    if not apiary:
        raise HTTPException(404, "Rucher introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(apiary, k, v)
    await log_action(db, user.id, "update", "apiary", apiary.id)
    return apiary


@router.delete("/{apiary_id}", status_code=204)
async def delete_apiary(
    apiary_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(Apiary).where(Apiary.id == apiary_id))
    apiary = result.scalar_one_or_none()
    if not apiary:
        raise HTTPException(404, "Rucher introuvable")
    await db.delete(apiary)
    await log_action(db, user.id, "delete", "apiary", apiary_id)


# ─── Ruches ─────────────────────────────────────────────

@router.get("/{apiary_id}/hives", response_model=list[HiveOut])
async def list_hives(apiary_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Hive).where(Hive.apiary_id == apiary_id).order_by(Hive.name))
    hives = result.scalars().all()
    return [_hive_out(h) for h in hives]


@router.get("/{apiary_id}/hives/editable", response_model=list[HiveOut])
async def list_editable_hives(
    apiary_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ruches actives que l'utilisateur courant peut visiter/modifier :
    - admin et yard_manager → toutes les ruches actives
    - autres → ruches associatives + ruches privées dont ils sont manager
    """
    from app.models.apiary import OwnershipType

    result = await db.execute(
        select(Hive).where(Hive.apiary_id == apiary_id, Hive.status == "active").order_by(Hive.name)
    )
    all_hives = result.scalars().all()

    roles = get_user_roles(user)
    if RoleEnum.ADMIN.value in roles or RoleEnum.YARD_MANAGER.value in roles:
        return [_hive_out(h) for h in all_hives]

    # Utilisateur simple → uniquement les ruches dont il est manager
    editable = [h for h in all_hives if any(m.id == user.id for m in h.managers)]
    return [_hive_out(h) for h in editable]


@router.post("/hives", response_model=HiveOut, status_code=201)
async def create_hive(
    body: HiveCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    data = body.model_dump(exclude={"manager_ids"})
    hive = Hive(**data)
    db.add(hive)
    await db.flush()

    if body.manager_ids:
        for uid in body.manager_ids:
            await db.execute(hive_managers.insert().values(user_id=uid, hive_id=hive.id))

    await log_action(db, user.id, "create", "hive", hive.id)
    await db.flush()

    # Recharger pour obtenir les managers
    await db.refresh(hive)
    return _hive_out(hive)


@router.put("/hives/{hive_id}", response_model=HiveOut)
async def update_hive(
    hive_id: int, body: HiveUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Hive).where(Hive.id == hive_id))
    hive = result.scalar_one_or_none()
    if not hive:
        raise HTTPException(404, "Ruche introuvable")

    # Vérification permissions : admin, yard_manager, ou manager de la ruche
    roles = get_user_roles(user)
    is_manager = any(m.id == user.id for m in hive.managers)
    if RoleEnum.ADMIN.value not in roles and RoleEnum.YARD_MANAGER.value not in roles and not is_manager:
        raise HTTPException(403, "Permissions insuffisantes")

    data = body.model_dump(exclude_unset=True, exclude={"manager_ids"})
    for k, v in data.items():
        setattr(hive, k, v)

    if body.manager_ids is not None:
        # Supprimer les anciens managers
        await db.execute(hive_managers.delete().where(hive_managers.c.hive_id == hive.id))
        for uid in body.manager_ids:
            await db.execute(hive_managers.insert().values(user_id=uid, hive_id=hive.id))

    await log_action(db, user.id, "update", "hive", hive.id)
    await db.flush()

    # Recharger pour obtenir les managers
    await db.refresh(hive)
    return _hive_out(hive)


@router.delete("/hives/{hive_id}", status_code=204)
async def delete_hive(
    hive_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(Hive).where(Hive.id == hive_id))
    hive = result.scalar_one_or_none()
    if not hive:
        raise HTTPException(404, "Ruche introuvable")
    await db.delete(hive)
    await log_action(db, user.id, "delete", "hive", hive_id)


@router.post("/hives/{hive_id}/photo", status_code=201)
async def upload_hive_photo(
    hive_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hive = await db.get(Hive, hive_id)
    if not hive:
        raise HTTPException(404, "Ruche introuvable")

    # Permission: admin, yard_manager, or manager
    roles = get_user_roles(user)
    is_manager = any(m.id == user.id for m in hive.managers)
    if RoleEnum.ADMIN.value not in roles and RoleEnum.YARD_MANAGER.value not in roles and not is_manager:
        raise HTTPException(403, "Permissions insuffisantes")

    upload_dir = get_settings().upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"hive_{hive_id}_{uuid.uuid4()}{ext}"
    path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # Remove old photo if present
    if hive.photo_path and os.path.exists(hive.photo_path):
        try: os.remove(hive.photo_path)
        except: pass

    hive.photo_path = path
    await log_action(db, user.id, "upload", "hive_photo", hive_id)
    await db.flush()
    return {"photo_url": f"/uploads/{filename}"}


@router.get("/hives/{hive_id}/photo")
async def get_hive_photo(hive_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    hive = await db.get(Hive, hive_id)
    if not hive or not hive.photo_path:
        raise HTTPException(404, "Photo introuvable")
    if not os.path.exists(hive.photo_path):
        raise HTTPException(404, "Photo manquante sur le serveur")
    return FileResponse(hive.photo_path, media_type="image/*")


@router.delete("/hives/{hive_id}/photo", status_code=204)
async def delete_hive_photo(hive_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    hive = await db.get(Hive, hive_id)
    if not hive or not hive.photo_path:
        raise HTTPException(404, "Photo introuvable")
    roles = get_user_roles(user)
    is_manager = any(m.id == user.id for m in hive.managers)
    if RoleEnum.ADMIN.value not in roles and RoleEnum.YARD_MANAGER.value not in roles and not is_manager:
        raise HTTPException(403, "Permissions insuffisantes")
    try:
        if os.path.exists(hive.photo_path): os.remove(hive.photo_path)
    except:
        pass
    hive.photo_path = None
    await log_action(db, user.id, "delete", "hive_photo", hive_id)
    await db.flush()


@router.get("/hives/{hive_id}/last-visit")
async def get_last_visit(
    hive_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retourne la dernière visite d'une ruche avec le nom de l'auteur."""
    result = await db.execute(
        select(Visit).where(Visit.hive_id == hive_id).order_by(desc(Visit.visited_at)).limit(1)
    )
    visit = result.scalar_one_or_none()
    if not visit:
        return None
    # Récupérer le nom de l'auteur
    author = await db.get(User, visit.author_id)
    return {
        "id": visit.id,
        "visited_at": visit.visited_at.isoformat(),
        "queen_seen": visit.queen_seen,
        "brood_score": visit.brood_score,
        "reserves_score": visit.reserves_score,
        "supers_delta": visit.supers_delta,
        "feeding": visit.feeding,
        "comment": visit.comment,
        "is_alert": visit.is_alert,
        "alert_message": visit.alert_message,
        "honey_harvest_kg": visit.honey_harvest_kg,
        "author_name": f"{author.first_name} {author.last_name}" if author else "Inconnu",
    }


def _hive_out(hive: Hive) -> HiveOut:
    own = hive.ownership.value if hasattr(hive.ownership, 'value') else (hive.ownership or 'associative')
    return HiveOut(
        id=hive.id,
        apiary_id=hive.apiary_id,
        napi_number=hive.napi_number,
        name=hive.name,
        ownership=own,
        position_x=hive.position_x,
        position_y=hive.position_y,
        status=hive.status,
        notes=hive.notes,
        managers=[{"id": m.id, "name": f"{m.first_name} {m.last_name}"} for m in hive.managers],
        created_at=hive.created_at,
        photo_url=(f"/uploads/{os.path.basename(hive.photo_path)}" if hive.photo_path else None),
    )
