"""Routes — Ruchers et Ruches."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models.apiary import Apiary, Hive, hive_managers
from app.models.visit import Visit
from app.models.user import User, RoleEnum
from app.schemas.apiary import (ApiaryCreate, ApiaryUpdate, ApiaryOut,
                                HiveCreate, HiveUpdate, HiveMove, HiveOut)
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
        data.photo_url = f"/uploads/{os.path.basename(a.photo_path)}" if a.photo_path else None
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


@router.post("/{apiary_id}/photo", status_code=201)
async def upload_apiary_photo(
    apiary_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    """Photo (aérienne) du rucher — sert aussi de fond au plan des ruches."""
    apiary = await db.get(Apiary, apiary_id)
    if not apiary:
        raise HTTPException(404, "Rucher introuvable")

    upload_dir = get_settings().upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"apiary_{apiary_id}_{uuid.uuid4()}{ext}"
    path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    if apiary.photo_path and os.path.exists(apiary.photo_path):
        try: os.remove(apiary.photo_path)
        except: pass

    apiary.photo_path = path
    await log_action(db, user.id, "upload", "apiary_photo", apiary_id)
    await db.flush()
    return {"photo_url": f"/uploads/{filename}"}


@router.delete("/{apiary_id}/photo", status_code=204)
async def delete_apiary_photo(
    apiary_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    apiary = await db.get(Apiary, apiary_id)
    if not apiary or not apiary.photo_path:
        raise HTTPException(404, "Photo introuvable")
    try:
        if os.path.exists(apiary.photo_path): os.remove(apiary.photo_path)
    except:
        pass
    apiary.photo_path = None
    await log_action(db, user.id, "delete", "apiary_photo", apiary_id)
    await db.flush()


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


@router.get("/hives/mine", response_model=list[HiveOut])
async def list_my_hives(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ruches actives dont l'utilisateur courant est propriétaire (gestionnaire),
    tous ruchers confondus. Utilisé par la « visite rapide »."""
    result = await db.execute(
        select(Hive)
        .join(hive_managers, hive_managers.c.hive_id == Hive.id)
        .where(hive_managers.c.user_id == user.id, Hive.status == "active")
        .order_by(Hive.apiary_id, Hive.name)
    )
    return [_hive_out(h) for h in result.scalars().all()]


@router.get("/hives/all", response_model=list[HiveOut])
async def list_all_hives(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Toutes les ruches actives, avec leur rucher — pour le signalement.

    Un adhérent doit pouvoir alerter sur n'importe quelle ruche, y compris une
    dont il n'a pas la charge : c'est justement le cas où le responsable doit
    être prévenu.
    """
    result = await db.execute(
        select(Hive, Apiary.name)
        .join(Apiary, Apiary.id == Hive.apiary_id)
        .where(Hive.status == "active")
        .order_by(Apiary.name, Hive.name)
    )
    out = []
    for hive, apiary_name in result.all():
        data = _hive_out(hive)
        data.apiary_name = apiary_name
        out.append(data)
    return out


def _clean_number(value) -> str | None:
    """Numéro normalisé ; une saisie vide vaut « pas de numéro »."""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


async def _check_number_available(db: AsyncSession, number: str | None,
                                  exclude_id: int = None) -> None:
    """Refuse un numéro de ruche déjà attribué.

    Attention : c'est le numéro **de la ruche** qui doit être unique, pas le
    NAPI. Le NAPI est le numéro d'apiculteur : il identifie le propriétaire
    auprès de l'administration, et toutes ses ruches le partagent.

    Le contrôle porte sur l'ensemble des ruchers, pas seulement le rucher
    courant : une ruche garde son numéro en changeant de rucher, un contrôle
    limité à un rucher créerait donc des doublons au premier déplacement.
    """
    if not number:
        return
    q = select(Hive).where(func.lower(Hive.number) == number.lower())
    if exclude_id:
        q = q.where(Hive.id != exclude_id)
    other = (await db.execute(q.limit(1))).scalar_one_or_none()
    if not other:
        return
    apiary = await db.get(Apiary, other.apiary_id)
    label = other.name or f"Ruche #{other.id}"
    where = f" du rucher « {apiary.name} »" if apiary else ""
    raise HTTPException(
        409,
        f"Le numéro « {number} » est déjà utilisé par la ruche « {label} »{where}.",
    )


@router.post("/hives", response_model=HiveOut, status_code=201)
async def create_hive(
    body: HiveCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    # « manager_ids » (table de liaison) et « photo » (upload dédié via
    # /hives/{id}/photo) ne sont pas des colonnes du modèle Hive.
    data = body.model_dump(exclude={"manager_ids", "photo"})
    data["number"] = _clean_number(data.get("number"))
    data["napi_number"] = _clean_number(data.get("napi_number"))
    await _check_number_available(db, data["number"])
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

    data = body.model_dump(exclude_unset=True, exclude={"manager_ids", "photo"})
    if "number" in data:
        data["number"] = _clean_number(data["number"])
        await _check_number_available(db, data["number"], exclude_id=hive.id)
    if "napi_number" in data:
        # Le NAPI est celui du propriétaire : aucune unicité à contrôler.
        data["napi_number"] = _clean_number(data["napi_number"])
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


@router.post("/hives/{hive_id}/move", response_model=HiveOut)
async def move_hive(
    hive_id: int,
    body: HiveMove,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    """Transfère une ruche vers un autre rucher (transhumance, réorganisation).

    Tout l'historique suit la ruche : visites, traitements, récoltes restent
    attachés à elle. Seule sa position sur le plan est effacée — elle désignait
    un emplacement sur la photo du rucher d'origine, qui n'a aucun sens sur le
    nouveau plan.
    """
    result = await db.execute(select(Hive).where(Hive.id == hive_id))
    hive = result.scalar_one_or_none()
    if not hive:
        raise HTTPException(404, "Ruche introuvable")

    target = await db.get(Apiary, body.apiary_id)
    if not target:
        raise HTTPException(404, "Rucher de destination introuvable")
    if hive.apiary_id == target.id:
        raise HTTPException(400, f"Cette ruche est déjà dans le rucher « {target.name} ».")

    origin = await db.get(Apiary, hive.apiary_id)
    origin_name = origin.name if origin else f"#{hive.apiary_id}"

    hive.apiary_id = target.id
    hive.position_x = None
    hive.position_y = None

    await log_action(db, user.id, "move", "hive", hive.id,
                     details=f"{origin_name} → {target.name}")
    await db.flush()
    await db.refresh(hive)
    out = _hive_out(hive)
    out.apiary_name = target.name
    return out


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
        "author_name": (f"{author.first_name or ''} {author.last_name or ''}".strip()
                        if author else "Inconnu"),
    }


def _hive_out(hive: Hive) -> HiveOut:
    own = hive.ownership.value if hasattr(hive.ownership, 'value') else (hive.ownership or 'associative')
    return HiveOut(
        id=hive.id,
        apiary_id=hive.apiary_id,
        number=hive.number,
        napi_number=hive.napi_number,
        name=hive.name,
        ownership=own,
        position_x=hive.position_x,
        position_y=hive.position_y,
        status=hive.status,
        notes=hive.notes,
        managers=[{"id": m.id,
                   # Sans « strip », un nom de famille vide donnait « Thomas  ».
                   "name": f"{m.first_name or ''} {m.last_name or ''}".strip() or m.email}
                  for m in hive.managers],
        created_at=hive.created_at,
        photo_url=(f"/uploads/{os.path.basename(hive.photo_path)}" if hive.photo_path else None),
    )
