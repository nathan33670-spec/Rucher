"""Routes — Journal des versions de l'application."""

from fastapi import APIRouter, Depends

from app.models.user import User
from app.releases import RELEASES, CURRENT_VERSION, latest
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/releases", tags=["releases"])


@router.get("/")
async def list_releases(user: User = Depends(get_current_user)):
    """Toutes les versions, la plus récente d'abord."""
    return {"current": CURRENT_VERSION, "releases": RELEASES}


@router.get("/current")
async def current_release(user: User = Depends(get_current_user)):
    return latest()
