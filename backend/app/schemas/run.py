from datetime import datetime
from enum import StrEnum
from typing import Literal, Optional

from pydantic import Field

from .common import Contract, BudgetUsage, ErrorInfo
from .intent import IntentType
from .plan import Plan
from .answer import FinalAnswer
from .verification import VerificationReport, Verdict
from .tools import ToolResult, ToolName, ToolArgs


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
    thread_id: Optional[str] = None


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
    note: Optional[str] = None


class RunSummary(Contract):
    id: str
    task: str
    status: RunStatus
    intent: Optional[IntentType] = None
    verdict: Optional[Verdict] = None
    verifier_score: Optional[float] = None
    budget: BudgetUsage
    created_at: datetime
    completed_at: Optional[datetime] = None


class RunDetail(RunSummary):
    plan: Optional[Plan] = None
    results: list[ToolResult] = Field(default_factory=list)
    answer: Optional[FinalAnswer] = None
    report: Optional[VerificationReport] = None
    error: Optional[ErrorInfo] = None
    langfuse_trace_url: Optional[str] = None


class ErrorResponse(Contract):
    error: ErrorInfo
    request_id: str