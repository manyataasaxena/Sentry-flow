from app.agents.guardrails import Guardrails
from app.core.llm_gateway import FakeLLM
from app.schemas.intent import IntentType


_PROMPT = "Explain the difference between weather and climate."


def test_weather_climate_prompt_is_not_flagged_by_guardrails_or_fake_intent() -> None:
    assert Guardrails.scan(_PROMPT) == []
    assert FakeLLM()._classify_intent(_PROMPT).intent != IntentType.UNSAFE
