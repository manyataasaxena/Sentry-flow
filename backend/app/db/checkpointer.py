from typing import Optional, Any

import asyncpg  # type: ignore[import-untyped]
from asyncpg.pool import PoolConnectionProxy  # type: ignore[import-untyped]

from ..core.config import settings
from ..core.logging import get_logger
from ..core.errors import SentryFlowError

from .postgres import postgres

logger = get_logger(__name__)


class CheckpointerAdapter:
    """LangGraph checkpointer adapter using PostgreSQL."""

    def __init__(self) -> None:
        self._conn: Optional[PoolConnectionProxy] = None

    async def setup(self) -> None:
        """Initialize checkpointer tables."""
        try:
            async with await postgres.get_connection() as conn:
                # Create checkpoints table
                await conn.executescript("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        thread_id TEXT NOT NULL,
                        checkpoint_id TEXT NOT NULL,
                        parent_checkpoint_id TEXT,
                        checkpoint JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        PRIMARY KEY (thread_id, checkpoint_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
                """)
                logger.info("Checkpointer tables initialized")
        except Exception as e:
            logger.error("Failed to setup checkpointer", error=str(e))
            raise SentryFlowError("Checkpointer setup failed", error_info={"error": str(e)})

    async def get(self, thread_id: str, checkpoint_id: str) -> Optional[dict[str, Any]]:
        """Get a specific checkpoint."""
        try:
            async with await postgres.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT checkpoint FROM checkpoints WHERE thread_id = $1 AND checkpoint_id = $2",
                    thread_id,
                    checkpoint_id,
                )
                return row["checkpoint"] if row else None
        except Exception as e:
            logger.error("Failed to get checkpoint", error=str(e))
            raise SentryFlowError("Get checkpoint failed", error_info={"error": str(e)})

    async def list(self, thread_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """List checkpoints for a thread."""
        try:
            async with await postgres.get_connection() as conn:
                rows = await conn.fetch(
                    "SELECT checkpoint_id, created_at FROM checkpoints WHERE thread_id = $1 ORDER BY created_at DESC LIMIT $2",
                    thread_id,
                    limit,
                )
                return [{"checkpoint_id": row["checkpoint_id"], "created_at": row["created_at"]} for row in rows]
        except Exception as e:
            logger.error("Failed to list checkpoints", error=str(e))
            raise SentryFlowError("List checkpoints failed", error_info={"error": str(e)})

    async def put(
        self,
        thread_id: str,
        checkpoint_id: str,
        checkpoint: dict[str, Any],
        parent_checkpoint_id: Optional[str] = None,
    ) -> None:
        """Put a checkpoint."""
        try:
            async with await postgres.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO checkpoints (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (thread_id, checkpoint_id) DO NOTHING
                    """,
                    thread_id,
                    checkpoint_id,
                    parent_checkpoint_id,
                    checkpoint,
                )
        except Exception as e:
            logger.error("Failed to put checkpoint", error=str(e))
            raise SentryFlowError("Put checkpoint failed", error_info={"error": str(e)})

    async def delete(self, thread_id: str, checkpoint_id: str) -> None:
        """Delete a checkpoint."""
        try:
            async with await postgres.get_connection() as conn:
                await conn.execute(
                    "DELETE FROM checkpoints WHERE thread_id = $1 AND checkpoint_id = $2",
                    thread_id,
                    checkpoint_id,
                )
        except Exception as e:
            logger.error("Failed to delete checkpoint", error=str(e))
            raise SentryFlowError("Delete checkpoint failed", error_info={"error": str(e)})

    async def health_check(self) -> bool:
        """Check if checkpointer is healthy."""
        try:
            async with await postgres.get_connection() as conn:
                await conn.fetchval("SELECT 1 FROM checkpoints LIMIT 1")
            return True
        except Exception:
            return False


# Global instance
checkpointer: CheckpointerAdapter = CheckpointerAdapter()