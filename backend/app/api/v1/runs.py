from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import get_current_user
from ...schemas.run import CreateRunRequest, RunSummary, RunDetail, ErrorResponse, ApprovalDecision, RunStatus
from ...schemas.common import BudgetUsage, ErrorInfo
from ...schemas.intent import IntentType
from ...schemas.verification import Verdict, VerificationReport
from ...schemas.plan import Plan
from ...schemas.answer import FinalAnswer
from ...schemas.tools import ToolResult
from ...schemas.events import RunEvent
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

# In-memory store for demo (would be replaced by database in production)
_runs: Dict[str, Dict[str, object]] = {}
_events: Dict[str, List[Dict[str, object]]] = {}


def _convert_intent(val: object) -> IntentType | None:
    if isinstance(val, str):
        return IntentType(val)
    if val is None:
        return None
    return val  # type: ignore[return-value]


def _convert_verdict(val: object) -> Verdict | None:
    if isinstance(val, str):
        return Verdict(val)
    if val is None:
        return None
    return val  # type: ignore[return-value]


def _convert_verifier_score(val: object) -> float | None:
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _convert_budget(val: object) -> BudgetUsage:
    if isinstance(val, BudgetUsage):
        return val
    return BudgetUsage()


def _convert_datetime(val: object, default: datetime | None = None) -> datetime | None:
    if isinstance(val, datetime):
        return val
    if val is None:
        return default
    return default


def _convert_plan(val: object) -> Plan | None:
    if isinstance(val, Plan):
        return val
    if val is None:
        return None
    return None


def _convert_results(val: object) -> list[ToolResult]:
    if isinstance(val, list):
        return val  # type: ignore[return-value]
    return []


def _convert_answer(val: object) -> FinalAnswer | None:
    if isinstance(val, FinalAnswer):
        return val
    if val is None:
        return None
    return None


def _convert_report(val: object) -> VerificationReport | None:
    if isinstance(val, VerificationReport):
        return val
    if val is None:
        return None
    return None


def _convert_error(val: object) -> ErrorInfo | None:
    if isinstance(val, ErrorInfo):
        return val
    if val is None:
        return None
    return None


def _convert_langfuse_url(val: object) -> str | None:
    if isinstance(val, str):
        return val
    if val is None:
        return None
    return None


@router.post("", response_model=RunSummary, status_code=202)
async def create_run(
    request: CreateRunRequest,
    current_user: dict[str, object] = Depends(get_current_user),
    idempotency_key: Optional[str] = Query(None, alias="Idempotency-Key"),
) -> RunSummary:
    """Create a new run."""
    run_id = f"run-{len(_runs) + 1}"

    # Check idempotency
    if idempotency_key and idempotency_key in _runs:
        existing = _runs[idempotency_key]
        return RunSummary(
            id=str(existing.get("id", "")),
            task=str(existing.get("task", "")),
            status=RunStatus(str(existing.get("status", "pending"))),
            intent=_convert_intent(existing.get("intent")),
            verdict=_convert_verdict(existing.get("verdict")),
            verifier_score=_convert_verifier_score(existing.get("verifier_score")),
            budget=_convert_budget(existing.get("budget")),
            created_at=_convert_datetime(existing.get("created_at"), datetime.now()),
            completed_at=_convert_datetime(existing.get("completed_at")),
        )

    run_data: Dict[str, object] = {
        "id": run_id,
        "task": request.task,
        "status": RunStatus.PENDING,
        "user_id": current_user.get("id"),
        "options": request.options,
        "created_at": datetime.now(),
        "budget": BudgetUsage(),
    }

    _runs[run_id] = run_data
    _events[run_id] = []

    logger.info("Run created", run_id=run_id, task=request.task[:50])

    return RunSummary(
        id=run_id,
        task=request.task,
        status=RunStatus.PENDING,
        intent=None,
        verdict=None,
        verifier_score=None,
        budget=BudgetUsage(),
        created_at=datetime.now(),
        completed_at=None,
    )


@router.get("", response_model=List[RunSummary])
async def list_runs(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict[str, object] = Depends(get_current_user),
) -> List[RunSummary]:
    """List runs with optional filters."""
    runs: List[RunSummary] = []
    for run_id, run_data in _runs.items():
        if user_id and run_data.get("user_id") != user_id:
            continue
        if status and run_data.get("status") != status:
            continue
        runs.append(RunSummary(
            id=str(run_data.get("id", "")),
            task=str(run_data.get("task", "")),
            status=RunStatus(str(run_data.get("status", "pending"))),
            intent=_convert_intent(run_data.get("intent")),
            verdict=_convert_verdict(run_data.get("verdict")),
            verifier_score=_convert_verifier_score(run_data.get("verifier_score")),
            budget=_convert_budget(run_data.get("budget")),
            created_at=_convert_datetime(run_data.get("created_at"), datetime.now()),
            completed_at=_convert_datetime(run_data.get("completed_at")),
        ))
    return runs


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str, current_user: dict[str, object] = Depends(get_current_user)) -> RunDetail:
    """Get run details."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunDetail(
        id=str(run_data.get("id", "")),
        task=str(run_data.get("task", "")),
        status=RunStatus(str(run_data.get("status", "pending"))),
        intent=_convert_intent(run_data.get("intent")),
        verdict=_convert_verdict(run_data.get("verdict")),
        verifier_score=_convert_verifier_score(run_data.get("verifier_score")),
        budget=_convert_budget(run_data.get("budget")),
        created_at=_convert_datetime(run_data.get("created_at"), datetime.now()),
        completed_at=_convert_datetime(run_data.get("completed_at")),
        plan=_convert_plan(run_data.get("plan")),
        results=_convert_results(run_data.get("results", [])),
        answer=_convert_answer(run_data.get("answer")),
        report=_convert_report(run_data.get("report")),
        error=_convert_error(run_data.get("error")),
        langfuse_trace_url=_convert_langfuse_url(run_data.get("langfuse_trace_url")),
    )


@router.get("/{run_id}/events")
async def get_run_events(run_id: str, after_seq: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Get run events for replay."""
    events = _events.get(run_id, [])
    if after_seq is not None:
        events = [e for e in events if e.get("seq", 0) > after_seq]
    return {"events": events}


@router.post("/{run_id}/approve", response_model=Dict[str, str])
async def approve_run(run_id: str, decision: ApprovalDecision, current_user: dict[str, object] = Depends(get_current_user)) -> Dict[str, str]:
    """Approve or reject a run."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    run_data["status"] = RunStatus.RUNNING if decision.approved else RunStatus.BLOCKED
    logger.info("Run approval", run_id=run_id, approved=decision.approved)

    return {"status": "approved" if decision.approved else "rejected"}


@router.post("/{run_id}/cancel", response_model=Dict[str, str])
async def cancel_run(run_id: str, current_user: dict[str, object] = Depends(get_current_user)) -> Dict[str, str]:
    """Cancel a running run."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    run_data["status"] = RunStatus.CANCELLED
    logger.info("Run cancelled", run_id=run_id)

    return {"status": "cancelled"}