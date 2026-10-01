from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from .answer import FinalAnswer
from .common import AgentName, Contract, ErrorInfo
from .plan import Plan
from .run import ApprovalRequest, RunStatus
from .tools import ToolName, ToolResult
from .verification import VerificationReport


class EventBase(Contract):
    seq: int
    run_id: str
    ts: datetime


class RunStarted(EventBase):
    type: Literal["run.started"] = "run.started"


class NodeStarted(EventBase):
    type: Literal["node.started"] = "node.started"
    node: AgentName


class NodeCompleted(EventBase):
    type: Literal["node.completed"] = "node.completed"
    node: AgentName
    duration_ms: int


class PlanCreated(EventBase):
    type: Literal["plan.created"] = "plan.created"
    plan: Plan


class ToolStarted(EventBase):
    type: Literal["tool.started"] = "tool.started"
    step_id: str
    tool: ToolName


class ToolCompleted(EventBase):
    type: Literal["tool.completed"] = "tool.completed"
    result: ToolResult


class VerifierReported(EventBase):
    type: Literal["verifier.report"] = "verifier.report"
    report: VerificationReport


class ApprovalRequested(EventBase):
    type: Literal["approval.requested"] = "approval.requested"
    request: ApprovalRequest


class BreakerChanged(EventBase):
    type: Literal["breaker.changed"] = "breaker.changed"
    dependency: str
    state: Literal["closed", "open", "half_open"]


class RunCompleted(EventBase):
    type: Literal["run.completed"] = "run.completed"
    status: RunStatus
    answer: FinalAnswer | None = None


class RunFailed(EventBase):
    type: Literal["run.failed"] = "run.failed"
    error: ErrorInfo


class Heartbeat(EventBase):
    type: Literal["heartbeat"] = "heartbeat"


RunEvent = Annotated[
    RunStarted
    | NodeStarted
    | NodeCompleted
    | PlanCreated
    | ToolStarted
    | ToolCompleted
    | VerifierReported
    | ApprovalRequested
    | BreakerChanged
    | RunCompleted
    | RunFailed
    | Heartbeat,
    Field(discriminator="type"),
]
