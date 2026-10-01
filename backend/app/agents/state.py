import operator
from typing import Annotated

from pydantic import BaseModel, Field

from ..schemas.answer import FinalAnswer
from ..schemas.common import BudgetUsage
from ..schemas.intent import IntentClassification
from ..schemas.plan import Plan
from ..schemas.run import ApprovalDecision, RunOptions, RunStatus
from ..schemas.tools import ToolResult
from ..schemas.verification import VerificationReport


class RunState(BaseModel):
    run_id: str
    task: str
    options: RunOptions
    intent: IntentClassification | None = None
    plan: Plan | None = None
    results: Annotated[list[ToolResult], operator.add] = Field(default_factory=list)
    approval: ApprovalDecision | None = None
    draft: FinalAnswer | None = None
    report: VerificationReport | None = None
    revision_count: int = 0
    status: RunStatus = RunStatus.RUNNING
    budget: BudgetUsage = Field(default_factory=BudgetUsage)


class StateUpdate(BaseModel):
    intent: IntentClassification | None = None
    plan: Plan | None = None
    results: list[ToolResult] | None = None
    approval: ApprovalDecision | None = None
    draft: FinalAnswer | None = None
    report: VerificationReport | None = None
    revision_count: int | None = None
    status: RunStatus | None = None
    budget: BudgetUsage | None = None


def as_update(update: StateUpdate) -> dict[str, object]:
    return update.model_dump(exclude_unset=True)
