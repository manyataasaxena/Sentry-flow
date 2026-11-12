from fastapi import APIRouter, Depends, HTTPException

from ...evals.runner import run_adversarial_suite
from ...schemas.evals import EvalReport
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/evals", tags=["evals"])
_eval_reports: dict[str, EvalReport] = {}


@router.post("/run", response_model=EvalReport)
async def run_evals(_current_user: dict[str, str] = Depends(get_current_user)) -> EvalReport:
    report = await run_adversarial_suite()
    _eval_reports[report.id] = report
    return report


@router.get("", response_model=list[EvalReport])
async def list_evals(_current_user: dict[str, str] = Depends(get_current_user)) -> list[EvalReport]:
    return list(_eval_reports.values())


@router.get("/{eval_id}", response_model=EvalReport)
async def get_eval(eval_id: str, _current_user: dict[str, str] = Depends(get_current_user)) -> EvalReport:
    report = _eval_reports.get(eval_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return report
