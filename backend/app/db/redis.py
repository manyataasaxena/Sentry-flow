import redis.asyncio as redis
from typing import Optional, Any

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class RedisAdapter:
    """Redis adapter for caching, pub/sub, and circuit breaker state."""

    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Test connection
        await self._client.ping()
        logger.info("Connected to Redis")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[str]:
            """Get value from Redis."""
            if not self._client:
                raise RuntimeError("Redis client not initialized")
            result = await self._client.get(key)
            return result if isinstance(result, str) else None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete key from Redis."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return bool(await self._client.exists(key))

    async def publish(self, channel: str, message: str) -> None:
        """Publish message to Redis channel."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        await self._client.publish(channel, message)

    async def subscribe(self, channel: str, callback) -> None:
        """Subscribe to Redis channel."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message["type"] == "message":
                await callback(message["data"])

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        try:
            if not self._client:
                return False
            await self._client.ping()
            return True
        except Exception:
            return False


# Global instance
redis_client = RedisAdapter()