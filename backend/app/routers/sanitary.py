"""Routes — Suivi sanitaire."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.sanitary import SanitaryRecord
from app.models.apiary import Hive
from app.models.user import User, RoleEnum
from app.schemas.sanitary import SanitaryCreate, SanitaryUpdate, SanitaryOut
from app.utils.auth import get_current_user, require_roles, get_user_roles
from app.utils.audit import log_action
from app.utils.push import notify

router = APIRouter(prefix="/api/sanitary", tags=["sanitary"])


def _record_out(r: SanitaryRecord) -> SanitaryOut:
    hive = r.hive
    return SanitaryOut(
        id=r.id,
        hive_id=r.hive_id,
        record_type=r.record_type or "treatment",
        treatment_type=r.treatment_type,
        product=r.product,
        dosage=r.dosage,
        application_date=r.application_date,
        end_date=r.end_date,
        varroa_count=r.varroa_count,
        notes=r.notes,
        performed_by=r.performed_by,
        created_at=r.created_at,
        hive_name=(hive.name or hive.napi_number or f"Ruche #{hive.id}") if hive else None,
    )


@router.get("/", response_model=list[SanitaryOut])
async def list_records(
    hive_id: int = None,
    record_type: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(SanitaryRecord).options(selectinload(SanitaryRecord.hive)).order_by(SanitaryRecord.application_date.desc()).limit(200)
    if hive_id:
        q = q.where(SanitaryRecord.hive_id == hive_id)
    if record_type:
        q = q.where(SanitaryRecord.record_type == record_type)
    result = await db.execute(q)
    return [_record_out(r) for r in result.scalars().all()]


@router.get("/hive/{hive_id}/summary")
async def hive_sanitary_summary(
    hive_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Resume sanitaire d une ruche : dernier traitement + dernier comptage varroa."""
    t_q = (
        select(SanitaryRecord)
        .where(SanitaryRecord.hive_id == hive_id, SanitaryRecord.record_type == "treatment")
        .order_by(desc(SanitaryRecord.application_date))
        .limit(1)
    )
    t_result = await db.execute(t_q)
    last_treatment = t_result.scalar_one_or_none()

    v_q = (
        select(SanitaryRecord)
        .where(SanitaryRecord.hive_id == hive_id, SanitaryRecord.record_type == "varroa_count")
        .order_by(desc(SanitaryRecord.application_date))
        .limit(1)
    )
    v_result = await db.execute(v_q)
    last_varroa = v_result.scalar_one_or_none()

    return {
        "last_treatment": {
            "treatment_type": last_treatment.treatment_type,
            "product": last_treatment.product,
            "date": last_treatment.application_date.isoformat(),
            "end_date": last_treatment.end_date.isoformat() if last_treatment.end_date else None,
        } if last_treatment else None,
        "last_varroa": {
            "varroa_count": last_varroa.varroa_count,
            "date": last_varroa.application_date.isoformat(),
            "notes": last_varroa.notes,
        } if last_varroa else None,
    }


@router.post("/", response_model=list[SanitaryOut], status_code=201)
async def create_record(
    body: SanitaryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Seuls admin/yard_manager peuvent créer des traitements ;
    # les utilisateurs normaux peuvent créer des comptages varroa sur leurs ruches
    user_roles = get_user_roles(user)
    is_manager = RoleEnum.ADMIN.value in user_roles or RoleEnum.YARD_MANAGER.value in user_roles
    if body.record_type == "treatment" and not is_manager:
        raise HTTPException(403, "Seuls les responsables peuvent enregistrer un traitement")

    hive_ids = list(body.hive_ids) if body.hive_ids else []
    if body.hive_id and body.hive_id not in hive_ids:
        hive_ids.append(body.hive_id)
    if not hive_ids:
        raise HTTPException(400, "Au moins une ruche est requise")

    # Vérifier l'accès aux ruches pour les utilisateurs normaux
    if not is_manager:
        for hid in hive_ids:
            hive = await db.get(Hive, hid)
            if not hive:
                raise HTTPException(404, f"Ruche {hid} introuvable")
            mgr_ids = [m.id for m in (hive.managers or [])]
            if user.id not in mgr_ids:
                raise HTTPException(403, f"Vous n'êtes pas responsable de la ruche {hid}")

    created = []
    for hid in hive_ids:
        record = SanitaryRecord(
            hive_id=hid,
            record_type=body.record_type or "treatment",
            treatment_type=body.treatment_type,
            product=body.product,
            dosage=body.dosage,
            application_date=body.application_date,
            end_date=body.end_date,
            varroa_count=body.varroa_count,
            notes=body.notes,
            performed_by=user.id,
        )
        db.add(record)
        await db.flush()
        await log_action(db, user.id, "create", "sanitary_record", record.id)
        # Recharger avec la relation hive
        result = await db.execute(
            select(SanitaryRecord).options(selectinload(SanitaryRecord.hive)).where(SanitaryRecord.id == record.id)
        )
        record = result.scalar_one()
        created.append(_record_out(record))
    if created:
        kind = "Comptage varroa" if body.record_type == "varroa_count" else "Traitement"
        notify("sanitary", "🩺 Sanitaire",
               f"{kind} enregistré sur {len(hive_ids)} ruche(s).", "/app/sanitary")
    return created


@router.put("/{record_id}", response_model=SanitaryOut)
async def update_record(
    record_id: int, body: SanitaryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN, RoleEnum.YARD_MANAGER)),
):
    record = await db.get(SanitaryRecord, record_id)
    if not record:
        raise HTTPException(404, "Enregistrement introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(record, k, v)
    await log_action(db, user.id, "update", "sanitary_record", record.id)
    result = await db.execute(
        select(SanitaryRecord).options(selectinload(SanitaryRecord.hive)).where(SanitaryRecord.id == record.id)
    )
    record = result.scalar_one()
    return _record_out(record)


@router.delete("/{record_id}", status_code=204)
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    record = await db.get(SanitaryRecord, record_id)
    if not record:
        raise HTTPException(404, "Enregistrement introuvable")
    await db.delete(record)
    await log_action(db, user.id, "delete", "sanitary_record", record_id)
