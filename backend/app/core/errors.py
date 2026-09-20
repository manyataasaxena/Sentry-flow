from enum import Enum
from typing import Any

from pydantic import BaseModel


class SentryFlowError(Exception):
    """Base error for all SentryFlow exceptions."""

    def __init__(self, message: str, *, error_info: dict[str, Any] | None = None):
        super().__init__(message)
        self.error_info = error_info or {}


class TransientError(SentryFlowError):
    """Errors that may succeed if retried (timeouts, 5xx, 429, connection errors)."""


class PermanentError(SentryFlowError):
    """Errors that will not succeed on retry (bad input, auth failures)."""


class CircuitOpenError(TransientError):
    """Raised when a circuit breaker is open."""


class GuardrailViolation(PermanentError):
    """Raised when input or output violates guardrails."""


class BudgetExceeded(PermanentError):
    """Raised when a run exceeds its token or cost budget."""


class ApprovalRejected(PermanentError):
    """Raised when a human rejects an approval request."""