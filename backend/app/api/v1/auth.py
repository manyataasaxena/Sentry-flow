from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any

from ..deps import get_current_user
from ...core.config import settings
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    pass


@router.post("/login")
async def login(request: LoginRequest) -> Dict[str, Any]:
    """Login with email and password."""
    if settings.AUTH_DISABLED:
        logger.info("Auth disabled, auto-login")
        return {"message": "Logged in (auth disabled)"}

    # In production, validate credentials
    return {"message": "Logged in"}


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """Logout."""
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(current_user: dict[str, object] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user."""
    return current_user