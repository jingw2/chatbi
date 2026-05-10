from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Mode: "postgres" (production) or "sqlite" (lite / local dev)
    db_mode: str = "postgres"

    # Infrastructure — PostgreSQL (only used when db_mode=postgres)
    postgres_db: str = "chatbi"
    postgres_user: str = "chatbi"
    postgres_password: str = "chatbi"
    postgres_host: str = "postgres"
    redis_password: str = "chatbi"

    # Infrastructure — SQLite (only used when db_mode=sqlite)
    sqlite_path: str = "data/chatbi.db"

    # Security
    secret_key: str = "dev_secret_key_change_in_production"
    encryption_key: str = "dev_encryption_key_32chars_padding"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # LLM — Intent Model
    intent_model_provider: str = "openai_compatible"
    intent_model_base_url: str = ""
    intent_model_name: str = "Qwen2.5-7B-Instruct"
    intent_model_api_key: str = "none"

    # LLM — Text-to-SQL Model
    text_to_sql_provider: str = "openai_compatible"
    text_to_sql_base_url: str = ""
    text_to_sql_model_name: str = "Qwen2.5-Coder-32B-Instruct"
    text_to_sql_api_key: str = "none"

    # LLM — Base Model
    base_model_provider: str = "anthropic"
    base_model_api_key: str = "none"
    base_model_name: str = "claude-sonnet-4-6"
    base_model_base_url: str = ""

    # Qdrant (only used when db_mode=postgres)
    qdrant_url: str = "http://qdrant:6333"

    # Embedding models (FlagEmbedding — installed via requirements-ml.txt)
    embedding_model_name: str = "BAAI/bge-m3"
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"

    @property
    def is_lite(self) -> bool:
        return self.db_mode == "sqlite"

    @property
    def database_url(self) -> str:
        if self.is_lite:
            db_path = Path(self.sqlite_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        if self.is_lite:
            return f"sqlite:///{self.sqlite_path}"
        return (
            f"postgresql://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}/{self.postgres_db}"
        )


settings = Settings()
