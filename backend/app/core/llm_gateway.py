from typing import Any, TypeVar

from pydantic import BaseModel

from ..core.config import settings
from ..core.errors import PermanentError
from ..core.logging import get_logger
from ..core.ports import LLMPort

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class FakeLLM(LLMPort):
    """Deterministic fake LLM for testing and demo mode."""

    def __init__(self) -> None:
        self._responses: dict[str, Any] = {}

    def register_response(self, purpose: str, response: Any) -> None:
        """Register a deterministic response for a purpose."""
        self._responses[purpose] = response

    async def structured(
        self,
        model: type[T],
        messages: list[dict[str, Any]],
        *,
        purpose: str,
    ) -> T:
        """Return a deterministic response based on purpose."""
        if purpose in self._responses:
            return model(**self._responses[purpose])

        # Return default response based on model type
        if model.__name__ == "IntentClassification":
            return model(intent="research", confidence=0.9, rationale="Default research intent")
        elif model.__name__ == "Plan":
            model_fields: dict[str, Any] = model.model_fields
            return model(
                intent=model_fields["intent"].default,
                steps=[],
                strategy_summary="Default plan",
                risk="low",
            )
        elif model.__name__ == "FinalAnswer":
            return model(answer="Default answer", citations=[], confidence=0.8)
        elif model.__name__ == "VerificationReport":
            return model(mode="output", verdict="pass", score=0.9, checks=[])
        else:
            return model()


class LLMGateway:
    """LLM gateway that selects the appropriate provider."""

    def __init__(self) -> None:
        self._fake_llm: LLMPort | None = FakeLLM()
        self._primary: LLMPort | None = None
        self._fallback: LLMPort | None = None

        if settings.MOCK_LLM:
            self._primary = self._fake_llm
            self._fallback = self._fake_llm
            logger.info("Using FakeLLM (mock mode)")
        else:
            # In production, initialize real LLM providers
            # self._primary = OpenAIGateway()
            # self._fallback = AnthropicGateway()
            logger.info("Using real LLM providers")

    @property
    def primary(self) -> LLMPort:
        """Get primary LLM provider."""
        if not self._primary:
            raise RuntimeError("No primary LLM provider configured")
        return self._primary

    @property
    def fallback(self) -> LLMPort:
        """Get fallback LLM provider."""
        if not self._fallback:
            raise RuntimeError("No fallback LLM provider configured")
        return self._fallback

    async def structured(
        self,
        model: type[T],
        messages: list[dict[str, Any]],
        *,
        purpose: str,
    ) -> T:
        """Call LLM with fallback chain."""
        try:
            return await self.primary.structured(model, messages, purpose=purpose)
        except Exception as e:
            logger.warning(f"Primary LLM failed, trying fallback: {e}")
            try:
                return await self.fallback.structured(model, messages, purpose=purpose)
            except Exception as fallback_error:
                logger.error(f"Fallback LLM also failed: {fallback_error}")
                error_info: dict[str, Any] = {"code": "LLM_FAILURE"}
                raise PermanentError(f"LLM call failed: {e}", error_info=error_info)


# Global instance
llm_gateway: LLMGateway = LLMGateway()
