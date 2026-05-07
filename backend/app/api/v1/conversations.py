from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.query_log import QueryLog
from app.models.user import User
from app.schemas.query_engine import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    QueryRequest,
    QueryResponse,
)
from app.api.deps import get_current_user
from app.query_engine.pipeline import run_pipeline

router = APIRouter(prefix="/conversations", tags=["conversations"])

_AUTO_TITLE_LENGTH = 30


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = Conversation(
        user_id=current_user.id,
        datasource_id=body.datasource_id,
        title=body.title or "New chat",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.patch("/{conv_id}", response_model=ConversationResponse)
async def rename_conversation(
    conv_id: int,
    body: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.title = body.title
    conv.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(conv)
    return conv


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()


@router.post("/{conv_id}/query", response_model=QueryResponse)
async def query_conversation(
    conv_id: int,
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the 9-step query pipeline and persist results to query_logs."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id)
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    pipeline_result = await run_pipeline(
        question=body.question,
        datasource_id=conv.datasource_id,
        user=current_user,
        db=db,
    )

    # Auto-title: set title to first 30 chars of question if still default
    if conv.title in ("New chat", "") or conv.title is None:
        conv.title = body.question[:_AUTO_TITLE_LENGTH]
        conv.updated_at = datetime.utcnow()

    # Write audit log
    log = QueryLog(
        conversation_id=conv.id,
        user_id=current_user.id,
        datasource_id=conv.datasource_id,
        user_question=body.question,
        intent=pipeline_result.intent,
        generated_sql=pipeline_result.sql,
        execution_ms=pipeline_result.execution_ms,
        row_count=len(pipeline_result.rows) if pipeline_result.rows else None,
        error_msg=pipeline_result.error,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return QueryResponse(
        query_log_id=log.id,
        intent=pipeline_result.intent,
        sql=pipeline_result.sql,
        columns=pipeline_result.columns,
        rows=pipeline_result.rows,
        chart_type=pipeline_result.chart_type,
        chart_config=pipeline_result.chart_config,
        insight=pipeline_result.insight,
        suggestions=pipeline_result.suggestions,
        warnings=pipeline_result.warnings,
        error=pipeline_result.error,
        execution_ms=pipeline_result.execution_ms,
    )
