from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.query_log import QueryLog
from app.models.user import User, UserRole

router = APIRouter(prefix="/audit", tags=["audit"])


class QueryLogResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    datasource_id: int | None
    user_question: str
    intent: str | None
    generated_sql: str | None
    execution_ms: int | None
    row_count: int | None
    error_msg: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/query-logs", response_model=list[QueryLogResponse])
async def list_query_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.superadmin, UserRole.admin)),
):
    limit = max(1, min(limit, 500))
    result = await db.execute(
        select(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
