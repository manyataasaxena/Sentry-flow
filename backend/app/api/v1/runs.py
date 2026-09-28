from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import get_current_user
from ...schemas.run import CreateRunRequest, RunSummary, RunDetail, ErrorResponse, ApprovalDecision
from ...schemas.events import RunEvent
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])

# In-memory store for demo (would be replaced by database in production)
_runs: Dict[str, Dict[str, Any]] = {}
_events: Dict[str, List[Dict[str, Any]]] = {}


@router.post("", response_model=RunSummary, status_code=202)
async def create_run(
    request: CreateRunRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    idempotency_key: Optional[str] = Query(None, alias="Idempotency-Key"),
) -> RunSummary:
    """Create a new run."""
    run_id = f"run-{len(_runs) + 1}"

    # Check idempotency
    if idempotency_key and idempotency_key in _runs:
        return RunSummary(**_runs[idempotency_key])

    run_data = {
        "id": run_id,
        "task": request.task,
        "status": "pending",
        "user_id": current_user["id"],
        "options": request.options.model_dump(),
        "created_at": "2024-01-01T00:00:00Z",
    }

    _runs[run_id] = run_data
    _events[run_id] = []

    logger.info("Run created", run_id=run_id, task=request.task[:50])

    return RunSummary(**run_data)


@router.get("", response_model=List[RunSummary])
async def list_runs(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[RunSummary]:
    """List runs with optional filters."""
    runs = []
    for run_id, run_data in _runs.items():
        if user_id and run_data.get("user_id") != user_id:
            continue
        if status and run_data.get("status") != status:
            continue
        runs.append(RunSummary(**run_data))
    return runs


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> RunDetail:
    """Get run details."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunDetail(**run_data)


@router.get("/{run_id}/events")
async def get_run_events(run_id: str, after_seq: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Get run events for replay."""
    events = _events.get(run_id, [])
    if after_seq:
        events = [e for e in events if e.get("seq", 0) > after_seq]
    return {"events": events}


@router.post("/{run_id}/approve", response_model=Dict[str, str])
async def approve_run(run_id: str, decision: ApprovalDecision, current_user: Dict = Depends(get_current_user)) -> Dict[str, str]:
    """Approve or reject a run."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    run_data["status"] = "running" if decision.approved else "blocked"
    logger.info("Run approval", run_id=run_id, approved=decision.approved)

    return {"status": "approved" if decision.approved else "rejected"}


@router.post("/{run_id}/cancel", response_model=Dict[str, str])
async def cancel_run(run_id: str, current_user: Dict = Depends(get_current_user)) -> Dict[str, str]:
    """Cancel a running run."""
    run_data = _runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    run_data["status"] = "cancelled"
    logger.info("Run cancelled", run_id=run_id)

    return {"status": "cancelled"}