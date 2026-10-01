from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...core.config import settings
from ...core.logging import get_logger
from ..deps import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    pass


@router.post("/login")
async def login(request: LoginRequest) -> dict[str, Any]:
    """Login with email and password."""
    if settings.AUTH_DISABLED:
        logger.info("Auth disabled, auto-login")
        return {"message": "Logged in (auth disabled)"}

    # In production, validate credentials
    return {"message": "Logged in"}


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout."""
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, Any]:
    """Get current user."""
    return current_user
