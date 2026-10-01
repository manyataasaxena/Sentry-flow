from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single application settings class. No other module reads os.environ."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True,
    )

    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    AUTH_DISABLED: bool = True
    JWT_SECRET: SecretStr = Field(default=SecretStr("sentryflow-insecure-dev-secret-key-32b"))
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Data connections
    POSTGRES_DSN: str = "postgresql://sentryflow:sentryflow@localhost:5432/sentryflow"
    REDIS_URL: str = "redis://localhost:6379/0"
    PG_POOL_MAX: int = 20

    # LLM configuration
    MOCK_LLM: bool = True
    PRIMARY_LLM: str = "openai:gpt-4o-mini"
    FALLBACK_LLM: str = "anthropic:claude-haiku-4-5-20251001"
    OPENAI_API_KEY: SecretStr | None = None
    ANTHROPIC_API_KEY: SecretStr | None = None

    # Observability
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: SecretStr | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Guardrails & budgets
    INTENT_MIN_CONFIDENCE: float = 0.55
    MAX_TOKENS_PER_RUN: int = 20000
    MAX_COST_USD_PER_RUN: float = 0.50
    RUN_TIMEOUT_SECONDS: int = 120
    HTTP_FETCH_ALLOWLIST: str = "example.com,wikipedia.org,github.com"
    CHAOS_ENABLED: bool = True
    SHUTDOWN_GRACE_SECONDS: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def http_fetch_allowlist(self) -> list[str]:
        return [domain.strip().lower() for domain in self.HTTP_FETCH_ALLOWLIST.split(",") if domain.strip()]

    @property
    def psycopg_dsn(self) -> str:
        """Derive psycopg connection string from POSTGRES_DSN."""
        if self.POSTGRES_DSN.startswith("postgresql+asyncpg://"):
            return self.POSTGRES_DSN.replace("postgresql+asyncpg://", "postgresql://", 1)
        return self.POSTGRES_DSN

    @property
    def asyncpg_dsn(self) -> str:
        """Derive asyncpg connection string for SQLAlchemy async engine."""
        if self.POSTGRES_DSN.startswith("postgresql://"):
            return self.POSTGRES_DSN.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.POSTGRES_DSN


settings = Settings()
