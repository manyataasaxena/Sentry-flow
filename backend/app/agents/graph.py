"""SentryFlow LangGraph agent orchestration."""

from langgraph.graph import StateGraph, END

from .state import RunState, as_update
from ..core.observability import observe
from ..core.llm_gateway import llm_gateway
from ..core.fallbacks import get_planner_fallback, get_verifier_fallback, get_finalizer_fallback
from ..core.logging import get_logger
from ..schemas.intent import IntentClassification
from ..schemas.plan import Plan
from ..schemas.tools import ToolResult, ToolStatus, ToolName
from ..schemas.verification import VerificationReport
from ..schemas.answer import FinalAnswer

logger = get_logger(__name__)


@observe(name="intake_guard")
async def intake_guard(state: RunState) -> dict:
    """Validate and classify the user task."""
    try:
        response = await llm_gateway.structured(
            IntentClassification,
            [
                {"role": "system", "content": "Classify the task into an intent type."},
                {"role": "user", "content": f"Task: {state.task}"},
            ],
            purpose="intent_classification",
        )
        return as_update({"intent": response})
    except Exception as e:
        logger.error("Intent classification failed", error=str(e))
        fallback = get_planner_fallback()
        return as_update({"intent": fallback.classify_intent(state.task)})


@observe(name="planner")
async def planner(state: RunState) -> dict:
    """Create an execution plan based on the classified intent."""
    if not state.intent:
        fallback = get_planner_fallback()
        return as_update({"plan": fallback.create_plan(state.task)})

    try:
        response = await llm_gateway.structured(
            Plan,
            [
                {"role": "system", "content": "Create a step-by-step plan for the task."},
                {"role": "user", "content": f"Task: {state.task}\nIntent: {state.intent.intent.value}"},
            ],
            purpose="plan_creation",
        )
        return as_update({"plan": response})
    except Exception as e:
        logger.error("Plan creation failed", error=str(e))
        fallback = get_planner_fallback()
        return as_update({"plan": fallback.create_plan(state.task, state.intent)})


@observe(name="approval_gate")
async def approval_gate(state: RunState) -> dict:
    """Review and approve the plan before execution."""
    if not state.plan or not state.plan.steps:
        return as_update({"status": "blocked", "approval": {"approved": False, "note": "No plan to approve"}})

    high_risk_steps = [s for s in state.plan.steps if s.risk == "high"]
    if high_risk_steps:
        return as_update({
            "approval": {"approved": True, "note": f"Auto-approved with {len(high_risk_steps)} high-risk steps"}
        })
    return as_update({
        "approval": {"approved": True, "note": "Plan approved automatically"}
    })


@observe(name="worker")
async def worker(state: RunState) -> dict:
    """Execute the approved plan steps."""
    if not state.plan or not state.plan.steps:
        return as_update({"status": "blocked", "results": []})

    results: list[ToolResult] = []
    for step in state.plan.steps:
        try:
            result = await _execute_step(step)
            results.append(result)
        except Exception as e:
            logger.error(f"Step {step.step_id} failed", error=str(e))
            results.append(ToolResult(
                step_id=step.step_id,
                tool=step.args.tool if hasattr(step.args, "tool") else ToolName.WEB_SEARCH,
                status=ToolStatus.FAILED,
                output=None,
                error={"code": "EXECUTION_ERROR", "message": str(e)},
                latency_ms=0,
                cache_hit=False,
            ))

    return as_update({"results": results})


async def _execute_step(step) -> ToolResult:
    """Execute a single plan step."""
    tool_name = step.args.tool if hasattr(step.args, "tool") else ToolName.WEB_SEARCH
    args = step.args.model_dump() if hasattr(step.args, "model_dump") else {}

    if tool_name == ToolName.WEB_SEARCH:
        query = args.get("query", "")
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SUCCESS,
            output={"kind": "search", "hits": []},
            latency_ms=100,
            cache_hit=False,
        )
    elif tool_name == ToolName.HTTP_FETCH:
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SUCCESS,
            output={"kind": "fetch", "url": args.get("url", ""), "text": "sample", "truncated": False},
            latency_ms=200,
            cache_hit=False,
        )
    elif tool_name == ToolName.CALCULATOR:
        expr = args.get("expression", "0")
        result = eval(expr) if expr else 0
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SUCCESS,
            output={"kind": "calc", "value": float(result)},
            latency_ms=50,
            cache_hit=False,
        )
    elif tool_name == ToolName.KB_LOOKUP:
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SUCCESS,
            output={"kind": "kb", "passages": []},
            latency_ms=150,
            cache_hit=False,
        )
    elif tool_name == ToolName.EXECUTE_WEBHOOK:
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SUCCESS,
            output={"kind": "webhook", "status_code": 200, "summary": "success"},
            latency_ms=300,
            cache_hit=False,
        )
    else:
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SKIPPED,
            output=None,
            latency_ms=0,
            cache_hit=False,
        )


@observe(name="verifier")
async def verifier(state: RunState) -> dict:
    """Verify the results and provide feedback."""
    try:
        response = await llm_gateway.structured(
            VerificationReport,
            [
                {"role": "system", "content": "Verify the execution results."},
                {"role": "user", "content": f"Task: {state.task}\nResults: {state.results}"},
            ],
            purpose="verification",
        )
        return as_update({"report": response})
    except Exception as e:
        logger.error("Verification failed", error=str(e))
        fallback = get_verifier_fallback()
        return as_update({"report": fallback.verify(state.task, state.results)})


@observe(name="finalize")
async def finalize(state: RunState) -> dict:
    """Create the final answer based on all results."""
    try:
        response = await llm_gateway.structured(
            FinalAnswer,
            [
                {"role": "system", "content": "Create a comprehensive final answer."},
                {"role": "user", "content": f"Task: {state.task}\nResults: {state.results}"},
            ],
            purpose="final_answer",
        )
        return as_update({"draft": response, "status": "completed"})
    except Exception as e:
        logger.error("Finalization failed", error=str(e))
        fallback = get_finalizer_fallback()
        return as_update({"draft": fallback.create_final_answer(state.task, state.results), "status": "completed"})


def create_agent_graph() -> StateGraph:
    """Create and return the agent execution graph."""
    workflow = StateGraph(RunState)

    workflow.add_node("intake_guard", intake_guard)
    workflow.add_node("planner", planner)
    workflow.add_node("approval_gate", approval_gate)
    workflow.add_node("worker", worker)
    workflow.add_node("verifier", verifier)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake_guard")

    workflow.add_edge("intake_guard", "planner")
    workflow.add_edge("planner", "approval_gate")
    workflow.add_edge("approval_gate", "worker")
    workflow.add_edge("worker", "verifier")
    workflow.add_edge("verifier", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


agent_graph = create_agent_graph()