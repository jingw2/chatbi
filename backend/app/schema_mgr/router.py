from __future__ import annotations
import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.models.user import User, UserRole
from app.schemas.schema_mgr import (
    TableResponse,
    TableUpdate,
    ColumnResponse,
    ColumnUpdate,
    SyncResponse,  # noqa: F401 — used in Task 4's sync endpoint
)
from app.api.deps import require_role
from app.embedding import embedding_service
from app.qdrant_store import qdrant_store

router = APIRouter(prefix="/schema", tags=["schema"])

_SCHEMA_COLLECTION = "schema_columns"
_admin_roles = (UserRole.superadmin, UserRole.admin)


def _column_text(table_name: str, col: SchemaColumn) -> str:
    """Build the text string to embed for a schema column."""
    parts = [f"{table_name}.{col.column_name} ({col.data_type})"]
    if col.description:
        parts.append(f": {col.description}")
    if col.example_values:
        parts.append(f". Examples: {col.example_values}")
    if col.notes:
        parts.append(f". Notes: {col.notes}")
    return "".join(parts)


@router.get("/{datasource_id}/tables", response_model=list[TableResponse])
async def list_tables(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(SchemaTable).where(SchemaTable.datasource_id == datasource_id)
    )
    return result.scalars().all()


@router.patch("/tables/{table_id}", response_model=TableResponse)
async def update_table(
    table_id: int,
    body: TableUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(select(SchemaTable).where(SchemaTable.id == table_id))
    table = result.scalar_one_or_none()
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    if body.description is not None:
        table.description = body.description
    if body.is_active is not None:
        table.is_active = body.is_active
    await db.commit()
    await db.refresh(table)
    return table


@router.get("/tables/{table_id}/columns", response_model=list[ColumnResponse])
async def list_columns(
    table_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(SchemaColumn).where(SchemaColumn.table_id == table_id)
    )
    return result.scalars().all()


@router.patch("/columns/{column_id}", response_model=ColumnResponse)
async def update_column(
    column_id: int,
    body: ColumnUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(SchemaColumn).where(SchemaColumn.id == column_id)
    )
    col = result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404, detail="Column not found")

    if body.description is not None:
        col.description = body.description
    if body.example_values is not None:
        col.example_values = body.example_values
    if body.notes is not None:
        col.notes = body.notes

    # Assign embedding_id before commit so it's persisted
    if col.embedding_id is None:
        col.embedding_id = str(uuid.uuid4())

    await db.commit()
    await db.refresh(col)

    # Re-embed in Qdrant after the DB commit succeeds
    table_result = await db.execute(
        select(SchemaTable).where(SchemaTable.id == col.table_id)
    )
    table = table_result.scalar_one_or_none()
    if table is not None:
        text = _column_text(table.table_name, col)
        vector = await asyncio.get_event_loop().run_in_executor(
            None, lambda: embedding_service.embed([text])[0]
        )
        await qdrant_store.ensure_collection(_SCHEMA_COLLECTION)
        await qdrant_store.upsert(
            _SCHEMA_COLLECTION,
            [
                {
                    "id": col.embedding_id,
                    "vector": vector,
                    "payload": {
                        "datasource_id": table.datasource_id,
                        "table_id": table.id,
                        "column_id": col.id,
                        "table_name": table.table_name,
                        "column_name": col.column_name,
                        "data_type": col.data_type,
                        "description": col.description,
                    },
                }
            ],
        )
    else:
        import logging
        logging.getLogger(__name__).warning(
            "update_column: table not found for col_id=%s table_id=%s — skipping Qdrant upsert",
            col.id, col.table_id,
        )

    return col
