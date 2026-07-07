"""Routes — Notifications push (abonnement, préférences, test)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.user import User
from app.models.notification import PushSubscription, NotificationPref
from app.schemas.notification import SubscribeIn, UnsubscribeIn, PrefsOut, PrefsUpdate
from app.utils.auth import get_current_user
from app.utils.push import get_or_create_vapid, send_push_to_user

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
    sent = await send_push_to_user(
        user.id, "🐝 Test Rucher",
        "Les notifications fonctionnent sur cet appareil !", "/app",
    )
    return {"sent": sent}
