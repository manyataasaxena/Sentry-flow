from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query

from ..deps import get_current_user
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

# Demo audit logs
_audit_logs: list[dict[str, Any]] = [
    {"id": 1, "actor_id": "admin", "action": "login", "target_type": "user", "target_id": "user-1", "created_at": "2024-01-01T00:00:00Z"},
    {"id": 2, "actor_id": "admin", "action": "run.created", "target_type": "run", "target_id": "run-1", "created_at": "2024-01-01T01:00:00Z"},
]


@router.get("", response_model=List[dict[str, Any]])
async def list_audit_logs(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> List[dict[str, Any]]:
    """List audit logs."""
    logs = _audit_logs
    if actor_id:
        logs = [l for l in logs if l.get("actor_id") == actor_id]
    if action:
        logs = [l for l in logs if l.get("action") == action]
    return logs