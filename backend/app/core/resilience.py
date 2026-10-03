import asyncio
import time
from collections.abc import Awaitable, Callable

from ..core.circuit_breaker import CircuitBreaker
from ..core.errors import CircuitOpenError, TransientError
from ..core.logging import get_logger

logger = get_logger(__name__)


class ResiliencePolicy:
    """Policy for resilience behavior."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_attempts: int = 3,
        backoff_multiplier: float = 0.5,
        backoff_max: float = 8.0,
        breaker_threshold: int = 5,
        breaker_recovery_timeout: int = 30,
    ):
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff_multiplier = backoff_multiplier
        self.backoff_max = backoff_max
        self.breaker_threshold = breaker_threshold
        self.breaker_recovery_timeout = breaker_recovery_timeout


async def resilient_call[T](
    dependency: str,
    fn: Callable[..., Awaitable[T]],
    *,
    policy: ResiliencePolicy | None = None,
    fallback: Callable[..., Awaitable[T]] | None = None,
    run_id: str | None = None,
) -> T:
    """Execute external call with circuit breaker, retry, timeout, and fallback.

    Composition order: fallback(retry(breaker(timeout(fn))))
    """
    policy = policy or ResiliencePolicy()
    breaker = CircuitBreaker(
        dependency,
        failure_threshold=policy.breaker_threshold,
        recovery_timeout=policy.breaker_recovery_timeout,
    )

    last_error: TransientError | None = None

    for attempt in range(policy.max_attempts):
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                breaker.call(fn),
                timeout=policy.timeout,
            )
            return result
        except TimeoutError:
            last_error = TransientError(f"Timeout on {dependency}", error_info={"code": "TIMEOUT", "dependency": dependency})
            logger.warning(f"Timeout on {dependency} (attempt {attempt + 1}/{policy.max_attempts})")
        except CircuitOpenError:
            last_error = TransientError(f"Circuit open for {dependency}", error_info={"code": "CIRCUIT_OPEN", "dependency": dependency})
            logger.warning(f"Circuit breaker open for {dependency}")
            break
        except TransientError as e:
            last_error = e
            logger.warning(f"Transient error on {dependency} (attempt {attempt + 1}/{policy.max_attempts})")
        except Exception as e:
            last_error = TransientError(f"Unexpected error on {dependency}", error_info={"code": "UNEXPECTED", "dependency": dependency})
            logger.error(f"Unexpected error on {dependency}: {e}")
            break

        # Exponential backoff with jitter
        if attempt < policy.max_attempts - 1:
            wait_time = min(policy.backoff_max, policy.backoff_multiplier * (2 ** attempt))
            jitter = wait_time * 0.1 * (2 * (time.time() % 1) - 1)  # ±10% jitter
            await asyncio.sleep(wait_time + jitter)

    # Try fallback
    if fallback:
        try:
            return await fallback()
        except Exception as e:
            logger.error(f"Fallback also failed for {dependency}: {e}")
            if last_error is not None:
                raise last_error from None
            raise TransientError(f"Fallback failed for {dependency}", error_info={"code": "FALLBACK_FAILED", "dependency": dependency}) from e

    if last_error is not None:
        raise last_error
    raise TransientError(f"LLM call failed for {dependency}", error_info={"code": "NO_ERROR", "dependency": dependency})
