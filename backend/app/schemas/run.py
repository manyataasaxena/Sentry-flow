from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field

from .answer import FinalAnswer
from .common import BudgetUsage, Contract, ErrorInfo
from .intent import IntentType
from .plan import Plan
from .tools import ToolArgs, ToolName, ToolResult
from .verification import Verdict, VerificationReport


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunOptions(Contract):
    max_steps: int = Field(default=8, ge=1, le=8)
    max_revisions: int = Field(default=2, ge=0, le=3)
    verifier_strictness: Literal["standard", "strict"] = "standard"
    approval_threshold: Literal["low", "medium", "high"] = "high"
    thread_id: str | None = None


class CreateRunRequest(Contract):
    task: str = Field(min_length=1, max_length=4000)
    options: RunOptions = Field(default_factory=RunOptions)


class ApprovalRequest(Contract):
    step_id: str
    tool: ToolName
    args: ToolArgs
    risk: Literal["low", "medium", "high"]
    reason: str


class ApprovalDecision(Contract):
    approved: bool
    note: str | None = None


class RunSummary(Contract):
    id: str
    task: str
    status: RunStatus
    intent: IntentType | None = None
    verdict: Verdict | None = None
    verifier_score: float | None = None
    budget: BudgetUsage
    created_at: datetime
    completed_at: datetime | None = None


class RunDetail(RunSummary):
    plan: Plan | None = None
    results: list[ToolResult] = Field(default_factory=list)
    answer: FinalAnswer | None = None
    report: VerificationReport | None = None
    error: ErrorInfo | None = None
    langfuse_trace_url: str | None = None


class ErrorResponse(Contract):
    error: ErrorInfo
    request_id: str
