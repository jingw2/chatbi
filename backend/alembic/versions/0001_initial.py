"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('superadmin', 'admin', 'analyst', 'viewer', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_table(
        'datasources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('db_type', sa.Enum('postgres', 'mysql', 'clickhouse', 'doris', name='dbtype'), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('encrypted_password', sa.String(500), nullable=False),
        sa.Column('readonly_user', sa.String(255), nullable=False),
        sa.Column('readonly_encrypted_password', sa.String(500), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'user_data_scopes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scope_key', sa.String(100), nullable=False),
        sa.Column('scope_value', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datasource_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schema_tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('datasource_id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('datasource_id', sa.Integer(), nullable=False),
        sa.Column('trigger_keywords', sa.JSON(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'knowledge_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('datasource_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('rule', 'fewshot', 'glossary', name='knowledgetype'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schema_columns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_id', sa.Integer(), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('data_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('example_values', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['table_id'], ['schema_tables.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'query_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('datasource_id', sa.Integer(), nullable=True),
        sa.Column('user_question', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('generated_sql', sa.Text(), nullable=True),
        sa.Column('execution_ms', sa.Integer(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('error_msg', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['datasource_id'], ['datasources.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('query_logs')
    op.drop_table('schema_columns')
    op.drop_table('knowledge_items')
    op.drop_table('workflows')
    op.drop_table('schema_tables')
    op.drop_table('conversations')
    op.drop_table('user_data_scopes')
    op.drop_table('datasources')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS dbtype")
    op.execute("DROP TYPE IF EXISTS knowledgetype")
