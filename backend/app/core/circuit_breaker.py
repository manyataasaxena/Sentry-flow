import asyncio
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, TypeVar

from ..core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async circuit breaker with Redis state sharing."""

    def __init__(self, dependency: str, failure_threshold: int = 5, recovery_timeout: int = 30) -> None:
        self.dependency = dependency
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_at: float | None = None
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.dependency} moving to HALF_OPEN")
                else:
                    from ..core.errors import CircuitOpenError
                    raise CircuitOpenError(f"Circuit breaker {self.dependency} is open")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._opened_at is None:
            return True
        return time.time() - self._opened_at > self.recovery_timeout

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._last_failure_at = None
            self._opened_at = None
            logger.info(f"Circuit breaker {self.dependency} closed")

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_at = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                logger.warning(f"Circuit breaker {self.dependency} opened after {self._failure_count} failures")

    async def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "dependency": self.dependency,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "last_failure_at": self._last_failure_at,
            "opens_at": self._opened_at,
        }
