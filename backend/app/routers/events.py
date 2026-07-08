"""Routes — Événements de l'association (création admin, RSVP adhérents)."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.database import get_db
from app.models.event import Event, EventRSVP
from app.models.user import User, RoleEnum
from app.schemas.event import (
    EventCreate, EventUpdate, EventOut, RSVPCounts, RSVPIn, ParticipantOut,
)
from app.utils.auth import get_current_user, require_roles, get_user_roles
from app.utils.audit import log_action
from app.utils.push import notify

router = APIRouter(prefix="/api/events", tags=["events"])


def _is_admin(user: User) -> bool:
    return RoleEnum.ADMIN.value in get_user_roles(user)


async def _counts_map(db: AsyncSession, event_ids: list[int]) -> dict[int, RSVPCounts]:
    """Agrège les réponses par événement en une seule requête."""
    out = {eid: RSVPCounts() for eid in event_ids}
    if not event_ids:
        return out
    res = await db.execute(
        select(EventRSVP.event_id, EventRSVP.response, func.count())
        .where(EventRSVP.event_id.in_(event_ids))
        .group_by(EventRSVP.event_id, EventRSVP.response)
    )
    for eid, response, n in res.all():
        c = out[eid]
        if response == "yes":
            c.yes = n
        elif response == "maybe":
            c.maybe = n
        elif response == "no":
            c.no = n
    return out


async def _my_responses(db: AsyncSession, event_ids: list[int], user_id: int) -> dict[int, str]:
    if not event_ids:
        return {}
    res = await db.execute(
        select(EventRSVP.event_id, EventRSVP.response).where(
            EventRSVP.event_id.in_(event_ids), EventRSVP.user_id == user_id
        )
    )
    return {eid: resp for eid, resp in res.all()}


def _to_out(ev: Event, my_resp: str | None, counts: RSVPCounts) -> EventOut:
    data = EventOut.model_validate(ev)
    data.my_response = my_resp
    data.counts = counts
    return data


@router.get("/", response_model=list[EventOut])
async def list_events(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Liste des événements, triés par date de début (les plus proches d'abord).

    - Admins : tous les événements (publics et privés).
    - Autres : uniquement les événements publics.
    """
    stmt = select(Event).order_by(Event.start_at.asc())
    if not _is_admin(user):
        stmt = stmt.where(Event.is_public.is_(True))
    events = list((await db.execute(stmt)).scalars().all())

    ids = [e.id for e in events]
    counts = await _counts_map(db, ids)
    mine = await _my_responses(db, ids, user.id)
    return [_to_out(e, mine.get(e.id), counts[e.id]) for e in events]


@router.post("/", response_model=EventOut, status_code=201)
async def create_event(
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    ev = Event(
        title=body.title,
        description=body.description,
        location=body.location,
        start_at=body.start_at,
        end_at=body.end_at,
        is_public=body.is_public,
        created_by=user.id,
    )
    db.add(ev)
    await db.flush()
    await log_action(db, user.id, "create", "event", ev.id)

    # Notification push à tous les adhérents abonnés (catégorie « events »),
    # uniquement pour un événement public dont l'admin a demandé la diffusion.
    if body.notify and body.is_public:
        when = body.start_at.strftime("%d/%m à %Hh%M")
        lieu = f" — {body.location}" if body.location else ""
        notify(
            "events",
            "📅 " + body.title,
            f"{when}{lieu}. Indiquez si vous venez.",
            "/app/events",
        )

    return _to_out(ev, None, RSVPCounts())


@router.put("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    body: EventUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Événement introuvable")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ev, k, v)
    await db.flush()
    await log_action(db, user.id, "update", "event", ev.id)

    counts = (await _counts_map(db, [ev.id]))[ev.id]
    mine = (await _my_responses(db, [ev.id], user.id)).get(ev.id)
    return _to_out(ev, mine, counts)


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Événement introuvable")
    await db.delete(ev)
    await log_action(db, user.id, "delete", "event", event_id)


@router.post("/{event_id}/rsvp", response_model=EventOut)
async def rsvp(
    event_id: int,
    body: RSVPIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Enregistre ou met à jour la réponse de l'utilisateur courant."""
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Événement introuvable")
    # Un adhérent ne peut répondre qu'à un événement public ; l'admin peut tout.
    if not ev.is_public and not _is_admin(user):
        raise HTTPException(403, "Événement non accessible")

    res = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id, EventRSVP.user_id == user.id
        )
    )
    entry = res.scalar_one_or_none()
    if entry:
        entry.response = body.response
    else:
        db.add(EventRSVP(event_id=event_id, user_id=user.id, response=body.response))
    await db.flush()

    counts = (await _counts_map(db, [event_id]))[event_id]
    return _to_out(ev, body.response, counts)


@router.get("/{event_id}/participants", response_model=list[ParticipantOut])
async def participants(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Liste des adhérents ayant répondu (réservé aux admins)."""
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Événement introuvable")
    res = await db.execute(
        select(EventRSVP, User)
        .join(User, User.id == EventRSVP.user_id)
        .where(EventRSVP.event_id == event_id)
        .order_by(EventRSVP.response, User.last_name)
    )
    out = []
    for r, u in res.all():
        out.append(ParticipantOut(
            user_id=u.id,
            name=f"{u.first_name} {u.last_name}".strip(),
            email=u.email,
            response=r.response,
            responded_at=r.responded_at,
        ))
    return out
