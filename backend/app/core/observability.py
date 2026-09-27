from typing import Optional, Callable, Any, TypeVar
from functools import wraps

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def redact(text: str) -> str:
    """Redact sensitive information from text."""
    if not text:
        return text

    # Redact API keys
    import re
    text = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\']?[^\s"\',]+', 'api_key=***REDACTED***', text, flags=re.IGNORECASE)
    text = re.sub(r'Bearer\s+[A-Za-z0-9._-]+', 'Bearer ***REDACTED***', text)

    # Redact emails
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***REDACTED_EMAIL***', text)

    # Redact phone numbers
    text = re.sub(r'\+?[1-9]\d{1,14}', '***REDACTED_PHONE***', text)

    return text


def observe(name: str, as_type: str = "generation") -> Callable[[F], F]:
    """Decorator for Langfuse observability.

    In mock mode, this is a no-op wrapper that still logs.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            run_id = kwargs.get("run_id") or (args[0].run_id if args and hasattr(args[0], 'run_id') else None)
            logger.info(f"@observe: {name}", run_id=run_id, type=as_type)

            # Redact inputs/outputs
            redacted_args = [redact(str(a)) if isinstance(a, str) else a for a in args]
            redacted_kwargs = {k: redact(str(v)) if isinstance(v, str) else v for k, v in kwargs.items()}

            try:
                result = await func(*redacted_args, **redacted_kwargs)
                logger.info(f"@observe completed: {name}", run_id=run_id, type=as_type)
                return result
            except Exception as e:
                logger.error(f"@observe error: {name}", run_id=run_id, type=as_type, error=str(e))
                raise
        return wrapper  # type: ignore[return-value]
    return decorator


def init_langfuse() -> Optional[Any]:
    """Initialize Langfuse client.

    Returns None if keys are not configured (no-op mode).
    """
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.info("Langfuse keys not configured, running in no-op mode")
        return None

    try:
        from langfuse import Langfuse
        langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY.get_secret_value(),
            host=settings.LANGFUSE_HOST,
        )
        logger.info("Langfuse initialized")
        return langfuse
    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return None


def post_score(run_id: str, score: float, verdict: str) -> None:
    """Post verifier score to Langfuse."""
    if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        logger.info(f"Posting score to Langfuse", run_id=run_id, score=score, verdict=verdict)
    # In production, would call langfuse.score()