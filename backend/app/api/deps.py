from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..core.config import settings
from ..core.errors import SentryFlowError

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, str]:
    """Get current user from JWT token."""
    if settings.AUTH_DISABLED:
        return {"id": "demo-user", "email": "demo@sentryflow.io", "role": "ADMIN"}

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # In production, validate JWT token
    return {"id": "user-id", "email": "user@example.com", "role": "VIEWER"}


async def get_settings() -> dict[str, Any]:
    """Get application settings."""
    result: dict[str, Any] = {
        "mock_llm": settings.MOCK_LLM,
        "environment": settings.ENVIRONMENT,
    }
    return result