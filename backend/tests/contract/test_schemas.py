"""Schema contract tests."""

import pytest

from app.schemas.common import (
    Contract,
    ErrorInfo,
    RiskLevel,
    Severity,
    AgentName,
    BudgetUsage,
)
from app.schemas.intent import IntentType, IntentClassification
from app.schemas.tools import (
    ToolName,
    ToolArgs,
    ToolResult,
    ToolSpec,
    WebSearchArgs,
    HttpFetchArgs,
    CalculatorArgs,
    KbLookupArgs,
    WebhookArgs,
)
from app.schemas.plan import Plan, PlanStep
from app.schemas.answer import Citation, FinalAnswer
from app.schemas.verification import Verdict, CheckType, CheckResult, VerificationReport
from app.schemas.run import (
    RunStatus,
    RunOptions,
    CreateRunRequest,
    ApprovalRequest,
    ApprovalDecision,
    RunSummary,
    RunDetail,
    ErrorResponse,
)
from app.schemas.events import (
    EventBase,
    RunStarted,
    NodeStarted,
    NodeCompleted,
    PlanCreated,
    ToolStarted,
    ToolCompleted,
    VerifierReported,
    ApprovalRequested,
    BreakerChanged,
    RunCompleted,
    RunFailed,
    Heartbeat,
    RunEvent,
)
from app.schemas.evals import (
    AttackCategory,
    ExpectedOutcome,
    AdversarialCase,
    EvalResult,
    EvalReport,
)
from app.schemas.system import BreakerStatus, HealthReport
from app.agents.state import RunState, StateUpdate, as_update


def test_contract_frozen_extra_forbid():
    assert Contract.model_config["frozen"] is True
    assert Contract.model_config["extra"] == "forbid"


def test_error_info_rejects_extra():
    with pytest.raises(Exception):
        ErrorInfo(code="X", message="m", extra_field="nope")  # type: ignore[call-arg]


def test_intent_classification_rejects_wrong_intent():
    with pytest.raises(Exception):
        IntentClassification(intent="unknown", confidence=0.5, rationale="x")  # type: ignore[call-arg]


def test_tool_args_discriminator_rejects_wrong_tool():
    with pytest.raises(Exception):
        ToolArgs(tool="unknown_tool", query="x")  # type: ignore[call-arg]


def test_web_search_args_valid():
    args = WebSearchArgs(query="hello")
    assert args.tool == "web_search"


def test_tool_result_rejects_extra():
    with pytest.raises(Exception):
        ToolResult(step_id="s1", tool="web_search", status="success", extra="nope")  # type: ignore[call-arg]


def test_plan_step_id_pattern():
    step = PlanStep(step_id="s1", goal="x", args=WebSearchArgs(query="xx"))
    assert step.step_id == "s1"


def test_plan_rejects_too_many_steps():
    steps = [PlanStep(step_id=f"s{i}", goal="x", args=WebSearchArgs(query="xx")) for i in range(9)]
    with pytest.raises(Exception):
        Plan(
            intent=IntentClassification(intent=IntentType.RESEARCH, confidence=0.9, rationale="x"),
            steps=steps,
            strategy_summary="x",
            risk=RiskLevel.LOW,
        )  # type: ignore[call-arg]


def test_final_answer_citation_step_id():
    ans = FinalAnswer(answer="x", citations=[Citation(step_id="s1", source="url")], confidence=0.9)
    assert ans.citations[0].step_id == "s1"


def test_verdict_enum():
    assert Verdict.PASS.value == "pass"


def test_check_result_rejects_extra():
    with pytest.raises(Exception):
        CheckResult(check="schema", passed=True, severity="info", detail="x", extra="nope")  # type: ignore[call-arg]


def test_run_status_enum():
    assert RunStatus.RUNNING.value == "running"


def test_run_options_defaults():
    opts = RunOptions()
    assert opts.max_steps == 8


def test_create_run_request_valid():
    req = CreateRunRequest(task="hello")
    assert req.task == "hello"


def test_approval_decision_valid():
    dec = ApprovalDecision(approved=True)
    assert dec.approved is True


def test_run_summary_rejects_extra():
    with pytest.raises(Exception):
        RunSummary(
            id="1",
            task="x",
            status="pending",
            budget=BudgetUsage(),
            created_at="2024-01-01T00:00:00Z",
            extra="nope",  # type: ignore[call-arg]
        )


def test_run_detail_rejects_extra():
    with pytest.raises(Exception):
        RunDetail(
            id="1",
            task="x",
            status="pending",
            budget=BudgetUsage(),
            created_at="2024-01-01T00:00:00Z",
            extra="nope",  # type: ignore[call-arg]
        )


def test_error_response_rejects_extra():
    with pytest.raises(Exception):
        ErrorResponse(
            error={"code": "X", "message": "m", "retryable": False, "dependency": None},
            request_id="r",
            extra="nope",  # type: ignore[call-arg]
        )


def test_event_discriminator_rejects_wrong_type():
    with pytest.raises(Exception):
        RunEvent(type="unknown.event", seq=1, run_id="r", ts="2024-01-01T00:00:00Z")  # type: ignore[call-arg]


def test_run_started_valid():
    ev = RunStarted(seq=1, run_id="r", ts="2024-01-01T00:00:00Z")
    assert ev.type == "run.started"


def test_node_started_requires_node():
    with pytest.raises(Exception):
        NodeStarted(seq=1, run_id="r", ts="2024-01-01T00:00:00Z")  # type: ignore[call-arg]


def test_node_completed_valid():
    ev = NodeCompleted(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", node="planner", duration_ms=100)
    assert ev.node == "planner"


def test_plan_created_valid():
    plan = Plan(
        intent=IntentClassification(intent=IntentType.RESEARCH, confidence=0.9, rationale="x"),
        steps=[PlanStep(step_id="s1", goal="x", args=WebSearchArgs(query="xx"))],
        strategy_summary="x",
        risk=RiskLevel.LOW,
    )
    ev = PlanCreated(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", plan=plan)
    assert ev.plan.steps[0].step_id == "s1"


def test_tool_started_valid():
    ev = ToolStarted(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", step_id="s1", tool="web_search")
    assert ev.tool == "web_search"


def test_tool_completed_valid():
    result = ToolResult(step_id="s1", tool="web_search", status="success", latency_ms=100)
    ev = ToolCompleted(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", result=result)
    assert ev.result.step_id == "s1"


def test_verifier_reported_valid():
    report = VerificationReport(
        verdict=Verdict.PASS,
        score=0.9,
        feedback="all good",
    )
    ev = VerifierReported(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", report=report)
    assert ev.report.verdict == "pass"


def test_approval_requested_valid():
    req = ApprovalRequest(step_id="s1", tool="web_search", args=WebhookArgs(endpoint_id="e1", payload_summary="x"), risk="high", reason="x")
    ev = ApprovalRequested(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", request=req)
    assert ev.request.step_id == "s1"


def test_breaker_changed_valid():
    ev = BreakerChanged(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", dependency="llm", state="open")
    assert ev.state == "open"


def test_run_completed_valid():
    ev = RunCompleted(seq=1, run_id="r", ts="2024-01-01T00:00:00Z", status="completed")
    assert ev.status == "completed"


def test_run_failed_valid():
    ev = RunFailed(
        seq=1,
        run_id="r",
        ts="2024-01-01T00:00:00Z",
        error=ErrorInfo(code="X", message="m", retryable=False, dependency=None),
    )
    assert ev.error.code == "X"


def test_heartbeat_valid():
    ev = Heartbeat(seq=1, run_id="r", ts="2024-01-01T00:00:00Z")
    assert ev.type == "heartbeat"


def test_attack_category_enum():
    assert AttackCategory.DIRECT_INJECTION.value == "direct_injection"


def test_expected_outcome_enum():
    assert ExpectedOutcome.BLOCK.value == "block"


def test_adversarial_case_valid():
    case = AdversarialCase(
        id="c1",
        category=AttackCategory.DIRECT_INJECTION,
        severity="critical",
        prompt="x",
        expected="block",
    )
    assert case.id == "c1"


def test_eval_result_valid():
    result = EvalResult(
        case_id="c1",
        category=AttackCategory.DIRECT_INJECTION,
        expected="block",
        actual="block",
        passed=True,
        latency_ms=100,
        detail="x",
    )
    assert result.passed is True


def test_eval_report_valid():
    report = EvalReport(
        id="e1",
        total=10,
        passed=9,
        pass_rate=0.9,
        critical_block_rate=1.0,
        false_positive_rate=0.0,
        by_category={},
        results=[],
    )
    assert report.pass_rate == 0.9


def test_breaker_status_valid():
    status = BreakerStatus(dependency="llm", state="closed", failure_count=0)
    assert status.state == "closed"


def test_health_report_valid():
    report = HealthReport(
        status="ok",
        postgres_ms=1.0,
        redis_ms=2.0,
        llm_primary="ok",
        breakers=[],
        chaos_enabled=False,
    )
    assert report.status == "ok"


def test_run_state_defaults():
    state = RunState(run_id="r", task="x", options=RunOptions())
    assert state.status == "running"
    assert state.revision_count == 0


def test_state_update_partial():
    update = StateUpdate(intent=None)
    assert update.intent is None


def test_as_update_excludes_unset():
    update = StateUpdate()
    dumped = as_update(update)
    assert "intent" not in dumped


def test_run_state_rejects_extra():
    with pytest.raises(Exception):
        RunState(run_id="r", task="x", extra="nope")  # type: ignore[call-arg]