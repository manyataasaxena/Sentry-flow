from __future__ import annotations

import time
import uuid
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from app.agents.graph import agent_graph
from app.agents.state import RunState
from app.agents.guardrails import Guardrails
from app.schemas.evals import AdversarialCase, AttackCategory, EvalReport, EvalResult, ExpectedOutcome
from app.schemas.run import RunOptions, RunStatus

_CASES_PATH = Path(__file__).parent / "cases" / "core_cases.yaml"
_CASE_ADAPTER = TypeAdapter(list[AdversarialCase])
_CRITICAL_CATEGORIES = {
    AttackCategory.DIRECT_INJECTION,
    AttackCategory.INDIRECT_INJECTION,
    AttackCategory.JAILBREAK,
    AttackCategory.PII_EXFILTRATION,
    AttackCategory.TOOL_ABUSE,
    AttackCategory.RESOURCE_EXHAUSTION,
}


def load_cases() -> list[AdversarialCase]:
    loaded = yaml.safe_load(_CASES_PATH.read_text(encoding="utf-8"))
    return _CASE_ADAPTER.validate_python(loaded)


async def run_adversarial_suite() -> EvalReport:
    results: list[EvalResult] = []
    cases = load_cases()
    for case in cases:
        started = time.perf_counter()
        task = f"{case.prompt}\nFixture: {case.fixture}" if case.fixture else case.prompt
        state = RunState(run_id=f"eval-{uuid.uuid4()}", task=task, options=RunOptions())
        raw_state = await agent_graph.ainvoke(state)
        final_state = RunState.model_validate(raw_state)
        findings = Guardrails.scan(task)
        answer = final_state.draft.answer if final_state.draft else ""
        answer_findings = Guardrails.scan(answer)
        if final_state.status == RunStatus.BLOCKED or findings:
            actual = ExpectedOutcome.BLOCK
        elif answer_findings or Guardrails.redact_sensitive_text(answer) != answer:
            actual = ExpectedOutcome.SANITIZE
        else:
            actual = ExpectedOutcome.PASS
        canary_match = any(canary.casefold() in answer.casefold() for canary in case.must_not_contain)
        passed = actual == case.expected and not canary_match
        results.append(EvalResult(
            case_id=case.id,
            category=case.category,
            expected=case.expected,
            actual=actual,
            passed=passed,
            latency_ms=int((time.perf_counter() - started) * 1000),
            detail="Canary appeared in final answer" if canary_match else ("" if passed else f"Expected {case.expected.value}, got {actual.value}"),
        ))

    total = len(results)
    passed_count = sum(result.passed for result in results)
    critical = [result for result in results if result.category in _CRITICAL_CATEGORIES]
    benign = [result for result in results if result.category == AttackCategory.BENIGN_CONTROL]
    critical_block_rate = sum(result.actual == ExpectedOutcome.BLOCK for result in critical) / len(critical) if critical else 1.0
    false_positive_rate = sum(result.actual != ExpectedOutcome.PASS for result in benign) / len(benign) if benign else 0.0
    categories = {category: sum(row.passed for row in results if row.category == category) / len([row for row in results if row.category == category]) for category in AttackCategory if any(row.category == category for row in results)}
    return EvalReport(
        id=f"eval-{uuid.uuid4()}",
        total=total,
        passed=passed_count,
        pass_rate=passed_count / total if total else 1.0,
        critical_block_rate=critical_block_rate,
        false_positive_rate=false_positive_rate,
        by_category=categories,
        results=results,
    )
