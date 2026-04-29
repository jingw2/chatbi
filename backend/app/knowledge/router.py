from __future__ import annotations
import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.knowledge_item import KnowledgeItem
from app.models.user import User, UserRole
from app.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItemResponse,
)
from app.api.deps import get_current_user, require_role
from app.embedding import embedding_service
from app.qdrant_store import qdrant_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_KB_COLLECTION = "knowledge_items"
_admin_roles = (UserRole.superadmin, UserRole.admin)


def _item_text(item: KnowledgeItem) -> str:
    return f"{item.title}\n\n{item.content}"


@router.get("", response_model=list[KnowledgeItemResponse])
async def list_knowledge(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.datasource_id == datasource_id)
    )
    return result.scalars().all()


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge(
    body: KnowledgeItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_admin_roles)),
):
    item = KnowledgeItem(
        datasource_id=body.datasource_id,
        type=body.type,
        title=body.title,
        content=body.content,
        embedding_id=str(uuid.uuid4()),
        created_by=current_user.id,
    )
    db.add(item)
    await db.flush()  # get item.id before embedding

    vector = await asyncio.get_running_loop().run_in_executor(
        None, lambda: embedding_service.embed([_item_text(item)])[0]
    )
    await qdrant_store.ensure_collection(_KB_COLLECTION)
    await qdrant_store.upsert(
        _KB_COLLECTION,
        [
            {
                "id": item.embedding_id,
                "vector": vector,
                "payload": {
                    "datasource_id": item.datasource_id,
                    "item_id": item.id,
                    "type": item.type.value,
                    "title": item.title,
                },
            }
        ],
    )

    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge(
    item_id: int,
    body: KnowledgeItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    if body.title is not None:
        item.title = body.title
    if body.content is not None:
        item.content = body.content

    if item.embedding_id is None:
        item.embedding_id = str(uuid.uuid4())

    await db.commit()
    await db.refresh(item)

    # Re-embed after commit (commit-before-qdrant ordering)
    vector = await asyncio.get_running_loop().run_in_executor(
        None, lambda: embedding_service.embed([_item_text(item)])[0]
    )
    await qdrant_store.ensure_collection(_KB_COLLECTION)
    await qdrant_store.upsert(
        _KB_COLLECTION,
        [
            {
                "id": item.embedding_id,
                "vector": vector,
                "payload": {
                    "datasource_id": item.datasource_id,
                    "item_id": item.id,
                    "type": item.type.value,
                    "title": item.title,
                },
            }
        ],
    )

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    if item.embedding_id:
        await qdrant_store.delete(_KB_COLLECTION, [item.embedding_id])

    await db.delete(item)
    await db.commit()
