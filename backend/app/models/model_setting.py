import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelRole(str, enum.Enum):
    intent = "intent"
    text_to_sql = "text_to_sql"
    base = "base"


class ModelProvider(str, enum.Enum):
    openai = "openai"
    anthropic = "anthropic"
    deepseek = "deepseek"
    qwen = "qwen"
    kimi = "kimi"
    glm = "glm"
    minimax = "minimax"
    gemini = "gemini"
    openai_compatible = "openai_compatible"  # generic / local vLLM


class ModelSetting(Base):
    __tablename__ = "model_settings"

    role: Mapped[ModelRole] = mapped_column(Enum(ModelRole), primary_key=True)
    provider: Mapped[ModelProvider] = mapped_column(Enum(ModelProvider), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
