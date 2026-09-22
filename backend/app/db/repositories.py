from typing import Optional, List, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..core.config import settings
from ..core.logging import get_logger
from ..core.errors import SentryFlowError

from .models import Base, Run, RunEvent, EvalRun, EvalResult, User, AuditLog, KbDocument

logger = get_logger(__name__)


class DatabaseRepository:
    """Repository for database operations."""

    def __init__(self) -> None:
        self._engine = create_async_engine(settings.asyncpg_dsn)
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self) -> None:
        """Initialize database and create tables."""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise SentryFlowError("Database initialization failed", error_info={"error": str(e)})

    async def close(self) -> None:
        """Close database connection."""
        await self._engine.dispose()

    async def health_check(self) -> bool:
        """Check if database is healthy."""
        try:
            async with self._session_factory() as session:
                await session.execute(select(1))
            return True
        except Exception:
            return False

    # Run operations
    async def create_run(self, run_data: dict) -> Run:
        """Create a new run."""
        async with self._session_factory() as session:
            run = Run(**run_data)
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run

    async def get_run(self, run_id: str) -> Optional[Run]:
        """Get a run by ID."""
        async with self._session_factory() as session:
            return await session.get(Run, run_id)

    async def update_run(self, run_id: str, update_data: dict) -> Optional[Run]:
        """Update a run."""
        async with self._session_factory() as session:
            run = await session.get(Run, run_id)
            if not run:
                return None
            for key, value in update_data.items():
                setattr(run, key, value)
            await session.commit()
            await session.refresh(run)
            return run

    async def list_runs(self, user_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Run]:
        """List runs with optional filters."""
        async with self._session_factory() as session:
            query = select(Run)
            if user_id:
                query = query.where(Run.user_id == user_id)
            if status:
                query = query.where(Run.status == status)
            query = query.order_by(Run.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def create_run_event(self, event_data: dict) -> RunEvent:
        """Create a run event."""
        async with self._session_factory() as session:
            event = RunEvent(**event_data)
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

    async def get_run_events(self, run_id: str, after_seq: Optional[int] = None, limit: int = 100) -> List[RunEvent]:
        """Get run events."""
        async with self._session_factory() as session:
            query = select(RunEvent).where(RunEvent.run_id == run_id)
            if after_seq:
                query = query.where(RunEvent.seq > after_seq)
            query = query.order_by(RunEvent.seq).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    # User operations
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        async with self._session_factory() as session:
            return await session.get(User, user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        async with self._session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()

    # KB operations
    async def search_kb(self, query: str, top_k: int = 10) -> List[KbDocument]:
        """Search KB documents."""
        async with self._session_factory() as session:
            # Simple text search for now - would use full-text search in production
            result = await session.execute(
                select(KbDocument).where(KbDocument.body.ilike(f"%{query}%")).limit(top_k)
            )
            return result.scalars().all()

    # Eval operations
    async def create_eval_run(self, eval_run_data: dict) -> EvalRun:
        """Create an eval run."""
        async with self._session_factory() as session:
            eval_run = EvalRun(**eval_run_data)
            session.add(eval_run)
            await session.commit()
            await session.refresh(eval_run)
            return eval_run

    async def create_eval_result(self, result_data: dict) -> EvalResult:
        """Create an eval result."""
        async with self._session_factory() as session:
            result = EvalResult(**result_data)
            session.add(result)
            await session.commit()
            await session.refresh(result)
            return result

    async def get_eval_run(self, eval_run_id: str) -> Optional[EvalRun]:
        """Get an eval run by ID."""
        async with self._session_factory() as session:
            return await session.get(EvalRun, eval_run_id)

    # Audit operations
    async def create_audit_log(self, audit_data: dict) -> AuditLog:
        """Create an audit log entry."""
        async with self._session_factory() as session:
            audit = AuditLog(**audit_data)
            session.add(audit)
            await session.commit()
            await session.refresh(audit)
            return audit

    async def list_audit_logs(self, actor_id: Optional[str] = None, action: Optional[str] = None, limit: int = 100) -> List[AuditLog]:
        """List audit logs with optional filters."""
        async with self._session_factory() as session:
            query = select(AuditLog)
            if actor_id:
                query = query.where(AuditLog.actor_id == actor_id)
            if action:
                query = query.where(AuditLog.action == action)
            query = query.order_by(AuditLog.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()


# Global instance
repository = DatabaseRepository()