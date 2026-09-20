import operator
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from ..schemas.common import RunStatus, BudgetUsage
from ..schemas.intent import IntentClassification
from ..schemas.plan import Plan
from ..schemas.answer import FinalAnswer
from ..schemas.verification import VerificationReport
from ..schemas.tools import ToolResult
from ..schemas.run import ApprovalDecision, RunOptions


class RunState(BaseModel):
    run_id: str
    task: str
    options: RunOptions
    intent: Optional[IntentClassification] = None
    plan: Optional[Plan] = None
    results: Annotated[list[ToolResult], operator.add] = Field(default_factory=list)
    approval: Optional[ApprovalDecision] = None
    draft: Optional[FinalAnswer] = None
    report: Optional[VerificationReport] = None
    revision_count: int = 0
    status: RunStatus = RunStatus.RUNNING
    budget: BudgetUsage = Field(default_factory=BudgetUsage)


class StateUpdate(BaseModel):
    intent: Optional[IntentClassification] = None
    plan: Optional[Plan] = None
    results: Optional[list[ToolResult]] = None
    approval: Optional[ApprovalDecision] = None
    draft: Optional[FinalAnswer] = None
    report: Optional[VerificationReport] = None
    revision_count: Optional[int] = None
    status: Optional[RunStatus] = None
    budget: Optional[BudgetUsage] = None


def as_update(update: StateUpdate) -> dict[str, object]:
    return update.model_dump(exclude_unset=True)