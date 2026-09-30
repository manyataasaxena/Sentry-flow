from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import get_current_user
from ...schemas.run import CreateRunRequest, RunSummary, RunDetail, ErrorResponse, ApprovalDecision, RunStatus
from ...schemas.common import BudgetUsage
from ...schemas.intent import IntentType
from ...schemas.verification import Verdict
from ...schemas.events import RunEvent
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

# In-memory store for demo (would be replaced by database in production)
_runs: Dict[str, Dict[str, object]] = {}
_events: Dict[str, List[Dict[str, object]]] = {}


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
        intent_val = existing.get("intent")
        intent = IntentType(intent_val) if isinstance(intent_val, str) else None if intent_val is None else intent_val
        verdict_val = existing.get("verdict")
        verdict = Verdict(verdict_val) if isinstance(verdict_val, str) else None if verdict_val is None else verdict_val
        verifier_score_val = existing.get("verifier_score")
        verifier_score = float(verifier_score_val) if isinstance(verifier_score_val, (int, float)) else None
        budget_val = existing.get("budget")
        budget = budget_val if isinstance(budget_val, BudgetUsage) else BudgetUsage()
        created_at_val = existing.get("created_at")
        created_at = created_at_val if isinstance(created_at_val, datetime) else datetime.now()
        completed_at_val = existing.get("completed_at")
        completed_at = completed_at_val if isinstance(completed_at_val, datetime) else None
        return RunSummary(
            id=str(existing.get("id", "")),
            task=str(existing.get("task", "")),
            status=RunStatus(str(existing.get("status", "pending"))),
            intent=intent,
            verdict=verdict,
            verifier_score=verifier_score,
            budget=budget,
            created_at=created_at,
            completed_at=completed_at,
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
        intent_val = run_data.get("intent")
        intent = IntentType(intent_val) if isinstance(intent_val, str) else None if intent_val is None else intent_val
        verdict_val = run_data.get("verdict")
        verdict = Verdict(verdict_val) if isinstance(verdict_val, str) else None if verdict_val is None else verdict_val
        verifier_score_val = run_data.get("verifier_score")
        verifier_score = float(verifier_score_val) if isinstance(verifier_score_val, (int, float)) else None
        budget_val = run_data.get("budget")
        budget = budget_val if isinstance(budget_val, BudgetUsage) else BudgetUsage()
        created_at_val = run_data.get("created_at")
        created_at = created_at_val if isinstance(created_at_val, datetime) else datetime.now()
        completed_at_val = run_data.get("completed_at")
        completed_at = completed_at_val if isinstance(completed_at_val, datetime) else None
        runs.append(RunSummary(
            id=str(run_data.get("id", "")),
            task=str(run_data.get("task", "")),
            status=RunStatus(str(run_data.get("status", "pending"))),
            intent=intent,
            verdict=verdict,
            verifier_score=verifier_score,
            budget=budget,
            created_at=created_at,
            completed_at=completed_at,
        ))
    return runs


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str, current_user: dict[str, object] = Depends(get_current_user)) -> RunDetail:
    """Get run details."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    intent_val = run_data.get("intent")
    intent = IntentType(intent_val) if isinstance(intent_val, str) else None if intent_val is None else intent_val
    verdict_val = run_data.get("verdict")
    verdict = Verdict(verdict_val) if isinstance(verdict_val, str) else None if verdict_val is None else verdict_val
    verifier_score_val = run_data.get("verifier_score")
    verifier_score = float(verifier_score_val) if isinstance(verifier_score_val, (int, float)) else None
    budget_val = run_data.get("budget")
    budget = budget_val if isinstance(budget_val, BudgetUsage) else BudgetUsage()
    created_at_val = run_data.get("created_at")
    created_at = created_at_val if isinstance(created_at_val, datetime) else datetime.now()
    completed_at_val = run_data.get("completed_at")
    completed_at = completed_at_val if isinstance(completed_at_val, datetime) else None
    plan_val = run_data.get("plan")
    results_val = run_data.get("results", [])
    answer_val = run_data.get("answer")
    report_val = run_data.get("report")
    error_val = run_data.get("error")
    langfuse_trace_url_val = run_data.get("langfuse_trace_url")
    return RunDetail(
        id=str(run_data.get("id", "")),
        task=str(run_data.get("task", "")),
        status=RunStatus(str(run_data.get("status", "pending"))),
        intent=intent,
        verdict=verdict,
        verifier_score=verifier_score,
        budget=budget,
        created_at=created_at,
        completed_at=completed_at,
        plan=plan_val,
        results=results_val,
        answer=answer_val,
        report=report_val,
        error=error_val,
        langfuse_trace_url=langfuse_trace_url_val,
    )


@router.get("/{run_id}/events")
async def get_run_events(run_id: str, after_seq: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Get run events for replay."""
    events = _events.get(run_id, [])
    if after_seq is not None:
        events = [e for e in events if (e.get("seq", 0) if isinstance(e.get("seq"), int) else 0) > after_seq]
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