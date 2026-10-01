from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # ADMIN, OPERATOR, VIEWER
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)  # Same as thread_id
    user_id = Column(String, nullable=False)
    task = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # PENDING, RUNNING, etc.
    intent = Column(JSON, nullable=True)
    plan = Column(JSON, nullable=True)
    answer = Column(JSON, nullable=True)
    report = Column(JSON, nullable=True)
    verdict = Column(String, nullable=True)
    verifier_score = Column(String, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    langfuse_trace_id = Column(String, nullable=True)
    prompt_versions = Column(JSON, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True)
    error = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_runs_user_id", user_id),
        Index("idx_runs_status", status),
        Index("idx_runs_created_at", created_at),
    )


class RunEvent(Base):
    __tablename__ = "run_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False)
    seq = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_run_events_run_id_seq", run_id, seq),
        Index("idx_run_events_run_id", run_id),
    )


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(String, primary_key=True)
    suite = Column(String, nullable=False)
    git_sha = Column(String, nullable=True)
    total = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)
    critical_block_rate = Column(Float, default=0.0)
    false_positive_rate = Column(Float, default=0.0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class EvalResult(Base):
    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    eval_run_id = Column(String, nullable=False)
    case_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    expected = Column(String, nullable=False)
    actual = Column(String, nullable=False)
    passed = Column(Boolean, nullable=False)
    latency_ms = Column(Integer, default=0)
    detail = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_eval_results_eval_run_id", eval_run_id),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    request_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    detail = Column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_actor_id", actor_id),
        Index("idx_audit_logs_action", action),
    )


class KbDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tsv = Column(Text, nullable=True)  # Full-text search vector

    __table_args__ = (
        Index("idx_kb_documents_tsv", tsv, postgresql_using="gin"),
    )
