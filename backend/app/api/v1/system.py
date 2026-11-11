from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from ...core.logging import get_logger
from ...schemas.common import BudgetUsage
from ...schemas.run import RunStatus
from ...schemas.system import BreakerStatus, HealthReport
from .runs import _runs
from ..deps import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["system"])

# Demo breaker states
_breakers: dict[str, dict[str, Any]] = {
    "llm-primary": {"state": "closed", "failure_count": 0, "last_failure_at": None, "opens_at": None},
    "llm-fallback": {"state": "closed", "failure_count": 0, "last_failure_at": None, "opens_at": None},
    "web_search": {"state": "closed", "failure_count": 0, "last_failure_at": None, "opens_at": None},
}

_chaos_enabled = False


@router.get("/health", response_model=HealthReport)
async def health_check(current_user: dict[str, Any] = Depends(get_current_user)) -> HealthReport:
    """Get system health report."""
    return HealthReport(
        status="ok",
        postgres_ms=1.5,
        redis_ms=0.8,
        llm_primary="ok",
        breakers=[BreakerStatus(**v) for v in _breakers.values()],
        chaos_enabled=_chaos_enabled,
    )


@router.get("/breakers", response_model=list[BreakerStatus])
async def list_breakers(current_user: dict[str, Any] = Depends(get_current_user)) -> list[BreakerStatus]:
    """List circuit breaker statuses."""
    return [BreakerStatus(**v) for v in _breakers.values()]


@router.post("/chaos")
async def toggle_chaos(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
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
async def metrics_summary(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, int | float]:
    """Compute dashboard metrics from stored runs."""
    now = datetime.now()
    runs_today = 0
    blocked_count = 0
    active_runs = 0
    completed_count = 0
    terminal_count = 0
    total_latency_ms = 0
    latency_run_count = 0
    total_cost_usd = 0.0

    for run_data in _runs.values():
        created_at = run_data.get("created_at")
        status = str(run_data.get("status", ""))
        if isinstance(created_at, datetime) and created_at.date() == now.date():
            runs_today += 1
        if status == RunStatus.BLOCKED.value:
            blocked_count += 1
        if status in {RunStatus.PENDING.value, RunStatus.RUNNING.value, RunStatus.AWAITING_APPROVAL.value}:
            active_runs += 1
        if status in {RunStatus.COMPLETED.value, RunStatus.BLOCKED.value, RunStatus.FAILED.value}:
            terminal_count += 1
            if status == RunStatus.COMPLETED.value:
                completed_count += 1

        completed_at = run_data.get("completed_at")
        if isinstance(created_at, datetime) and isinstance(completed_at, datetime):
            total_latency_ms += int((completed_at - created_at).total_seconds() * 1000)
            latency_run_count += 1

        budget = run_data.get("budget")
        if isinstance(budget, BudgetUsage):
            total_cost_usd += budget.cost_usd
        elif isinstance(budget, dict):
            cost = budget.get("cost_usd", 0.0)
            if isinstance(cost, (int, float)):
                total_cost_usd += float(cost)

    return {
        "runs_today": runs_today,
        "success_rate": completed_count / terminal_count * 100 if terminal_count else 0.0,
        "blocked_count": blocked_count,
        "avg_latency_ms": total_latency_ms / latency_run_count if latency_run_count else 0.0,
        "active_runs": active_runs,
        "total_cost_usd": total_cost_usd,
    }
