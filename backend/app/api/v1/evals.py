from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ...core.logging import get_logger
from ...schemas.evals import EvalReport
from ..deps import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])

# Demo eval data
_eval_runs: dict[str, dict[str, Any]] = {}
_eval_results: list[dict[str, Any]] = []


@router.post("/run", response_model=dict[str, Any], status_code=202)
async def run_evals(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Start adversarial evaluation suite."""
    eval_id = f"eval-{len(_eval_runs) + 1}"
    _eval_runs[eval_id] = {
        "id": eval_id,
        "total": 60,
        "passed": 0,
        "pass_rate": 0.0,
        "critical_block_rate": 0.0,
        "false_positive_rate": 0.0,
        "status": "running",
    }
    logger.info("Eval run started", eval_id=eval_id)
    return {"eval_run_id": eval_id, "status": "running"}


@router.get("", response_model=list[dict[str, Any]])
async def list_evals(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    """List evaluation runs."""
    return list(_eval_runs.values())


@router.get("/{eval_id}", response_model=EvalReport)
async def get_eval(eval_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> EvalReport:
    """Get evaluation report."""
    eval_data = _eval_runs.get(eval_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Eval run not found")

    return EvalReport(
        id=eval_id,
        total=eval_data["total"],
        passed=eval_data["passed"],
        pass_rate=eval_data["pass_rate"],
        critical_block_rate=eval_data["critical_block_rate"],
        false_positive_rate=eval_data["false_positive_rate"],
        by_category={},
        results=[],
    )
