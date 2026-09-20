from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_current_user
from ...schemas.system import BreakerStatus, HealthReport
from ...core.logging import get_logger
from ...core.circuit_breaker import CircuitBreaker, CircuitState

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["system"])

# Demo breaker states
_breakers: dict[str, dict] = {
    "llm-primary": {"state": "closed", "failure_count": 0, "last_failure_at": None, "opens_at": None},
    "llm-fallback": {"state": "closed", "failure_count": 0, "last_failure_at": None, "opens_at": None},
    "web_search": {"state": "closed", "failure_count": 0, "last_failure_at": None, "opens_at": None},
}

_chaos_enabled = False


@router.get("/health", response_model=HealthReport)
async def health_check(current_user: dict = Depends(get_current_user)):
    """Get system health report."""
    return HealthReport(
        status="ok",
        postgres_ms=1.5,
        redis_ms=0.8,
        llm_primary="ok",
        breakers=[BreakerStatus(**v) for v in _breakers.values()],
        chaos_enabled=_chaos_enabled,
    )


@router.get("/breakers", response_model=List[BreakerStatus])
async def list_breakers(current_user: dict = Depends(get_current_user)):
    """List circuit breaker statuses."""
    return [BreakerStatus(**v) for v in _breakers.values()]


@router.post("/chaos")
async def toggle_chaos(current_user: dict = Depends(get_current_user)):
    """Toggle chaos mode (demo only)."""
    global _chaos_enabled
    _chaos_enabled = not _chaos_enabled

    if _chaos_enabled:
        _breakers["llm-primary"]["state"] = "open"
        logger.warning("Chaos mode enabled - LLM primary breaker opened")
    else:
        _breakers["llm-primary"]["state"] = "closed"
        logger.info("Chaos mode disabled - LLM primary breaker closed")

    return {"chaos_enabled": _chaos_enabled}


@router.get("/metrics/summary")
async def metrics_summary(current_user: dict = Depends(get_current_user)):
    """Get system metrics summary."""
    return {
        "total_runs": 0,
        "active_runs": 0,
        "avg_latency_ms": 1200,
        "p95_latency_ms": 3500,
        "total_cost_usd": 0.0,
        "uptime_seconds": 3600,
    }