"""Routes — Notifications push (abonnement, préférences, test)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.database import get_db
from app.models.user import User, RoleEnum
from app.models.notification import PushSubscription, NotificationPref
from app.schemas.notification import SubscribeIn, UnsubscribeIn, PrefsOut, PrefsUpdate
from app.utils.auth import get_current_user, require_roles
from app.utils.push import (get_or_create_vapid, send_push_to_user,
                            resolve_vapid_subject, LAST_RESULT)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/vapid-public-key")
async def vapid_public_key(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _priv, pub = await get_or_create_vapid(db)
    return {"publicKey": pub}


@router.post("/subscribe", status_code=201)
async def subscribe(
    body: SubscribeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(PushSubscription).where(PushSubscription.endpoint == body.endpoint))
    sub = result.scalar_one_or_none()
    if sub:
        sub.user_id = user.id
        sub.p256dh = body.keys.p256dh
        sub.auth = body.keys.auth
    else:
        db.add(PushSubscription(
            user_id=user.id, endpoint=body.endpoint,
            p256dh=body.keys.p256dh, auth=body.keys.auth,
        ))
    # crée les préférences par défaut si absentes
    await _get_or_create_prefs(db, user.id)
    return {"detail": "abonné"}


@router.post("/unsubscribe")
async def unsubscribe(
    body: UnsubscribeIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.endpoint == body.endpoint,
            PushSubscription.user_id == user.id,
        )
    )
    return {"detail": "désabonné"}


async def _get_or_create_prefs(db: AsyncSession, user_id: int) -> NotificationPref:
    result = await db.execute(select(NotificationPref).where(NotificationPref.user_id == user_id))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = NotificationPref(user_id=user_id)
        db.add(prefs)
        await db.flush()
    return prefs


@router.get("/preferences", response_model=PrefsOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _get_or_create_prefs(db, user.id)


@router.put("/preferences", response_model=PrefsOut)
async def update_preferences(
    body: PrefsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prefs = await _get_or_create_prefs(db, user.id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    await db.flush()
    await db.refresh(prefs)
    return prefs


@router.post("/test")
async def test_notification(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Envoie une notification de test et dit précisément ce qui s'est passé.

    Renvoyer un simple compteur laissait croire à un succès alors qu'aucun
    appareil n'était abonné : le message est désormais explicite.
    """
    devices = await db.scalar(
        select(func.count()).select_from(PushSubscription)
        .where(PushSubscription.user_id == user.id)
    ) or 0
    if devices == 0:
        return {
            "sent": 0, "devices": 0,
            "detail": ("Aucun appareil abonné sur ce compte. Activez les "
                       "notifications ci-dessus, depuis l'appareil concerné."),
        }
    sent = await send_push_to_user(
        user.id, "🐝 Test Rucher",
        "Les notifications fonctionnent sur cet appareil !", "/app",
    )
    if sent == 0:
        return {
            "sent": 0, "devices": devices,
            "detail": (f"{devices} appareil(s) enregistré(s) mais aucun n'a "
                       "accepté le message. Désactivez puis réactivez les "
                       "notifications sur cet appareil."),
        }
    return {"sent": sent, "devices": devices,
            "detail": f"Notification envoyée à {sent} appareil(s)."}


@router.get("/diagnostics")
async def diagnostics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """État réel du service de notifications, pour l'administrateur.

    Sans cette vue, « les notifications ne marchent pas » est indiagnosticable :
    on ne sait pas distinguer un serveur muet d'un parc sans abonnement.
    """
    _priv, pub = await get_or_create_vapid(db)
    subject = await resolve_vapid_subject(db)

    res = await db.execute(
        select(User.id, User.first_name, User.last_name,
               func.count(PushSubscription.id).label("devices"))
        .outerjoin(PushSubscription, PushSubscription.user_id == User.id)
        .where(User.is_active.is_(True))
        .group_by(User.id, User.first_name, User.last_name)
        .order_by(User.last_name)
    )
    rows = res.all()

    res = await db.execute(select(NotificationPref))
    prefs = {p.user_id: p for p in res.scalars().all()}

    users = []
    for r in rows:
        p = prefs.get(r.id)
        users.append({
            "id": r.id,
            "name": f"{r.first_name} {r.last_name}".strip(),
            "devices": r.devices,
            # Sans ligne de préférences, l'utilisateur ne reçoit rien : c'est
            # justement l'une des causes de « ça ne marche pas ».
            "enabled": bool(p.enabled) if p else None,
            "categories": ([c for c in ("visits", "inventory", "alerts",
                                        "sanitary", "treasury", "events")
                            if p and getattr(p, c)] if p else []),
        })

    total_devices = sum(u["devices"] for u in users)
    return {
        "vapid_configured": bool(pub),
        "vapid_public_key": (pub[:12] + "…") if pub else None,
        # Contact exigé par le protocole : s'il est invalide, aucun envoi n'aboutit.
        "vapid_subject": subject,
        "total_devices": total_devices,
        "users_with_device": sum(1 for u in users if u["devices"]),
        "users_without_prefs": [u["name"] for u in users if u["enabled"] is None],
        "last_send": LAST_RESULT or None,
        "users": users,
    }
