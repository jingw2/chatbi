"""model settings

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_settings",
        sa.Column("role", sa.Enum("intent", "text_to_sql", "base", name="modelrole"), nullable=False),
        sa.Column("provider", sa.Enum("openai", "openai_compatible", "anthropic", name="modelprovider"), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("encrypted_api_key", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("role"),
    )


def downgrade() -> None:
    op.drop_table("model_settings")
    op.execute("DROP TYPE IF EXISTS modelprovider")
    op.execute("DROP TYPE IF EXISTS modelrole")
