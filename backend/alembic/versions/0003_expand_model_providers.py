"""expand modelprovider enum with new vendors

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-12

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_VALUES = ("deepseek", "qwen", "kimi", "glm", "minimax", "gemini")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for value in _NEW_VALUES:
            op.execute(f"ALTER TYPE modelprovider ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    pass
