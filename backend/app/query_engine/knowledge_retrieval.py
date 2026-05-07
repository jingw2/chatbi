from __future__ import annotations

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.knowledge_item import KnowledgeItem
from app.embedding import embedding_service
from app.qdrant_store import qdrant_store

_KB_COLLECTION = "knowledge_items"
_CANDIDATE_COUNT = 20


async def retrieve_knowledge(
    query: str,
    datasource_id: int,
    db: AsyncSession,
    top_k: int = 5,
) -> list[dict]:
    """Return top-k knowledge items most relevant to the query.

    Pipeline: embed query → Qdrant top-20 (filtered by datasource_id)
              → bge-reranker top-k → fetch full records from DB.

    Returns list of dicts with keys: id, type, title, content
    Returns [] if no embeddings exist for the datasource.
    """
    query_vector = await asyncio.get_running_loop().run_in_executor(
        None, lambda: embedding_service.embed([query])[0]
    )

    hits = await qdrant_store.search(
        _KB_COLLECTION,
        query_vector,
        top_k=_CANDIDATE_COUNT,
        filter_={"datasource_id": datasource_id},
    )
    if not hits:
        return []

    passages = [
        f"{h['payload'].get('title', '')}: {h['payload'].get('type', '')}"
        for h in hits
    ]
    scores = await asyncio.get_running_loop().run_in_executor(
        None, lambda: embedding_service.rerank(query, passages)
    )
    ranked = sorted(zip(scores, hits), key=lambda x: x[0], reverse=True)[:top_k]
    item_ids = [int(r[1]["payload"]["item_id"]) for r in ranked]

    rows = await db.execute(
        select(KnowledgeItem).where(KnowledgeItem.id.in_(item_ids))
    )
    items = {item.id: item for item in rows.scalars().all()}

    return [
        {
            "id": items[iid].id,
            "type": items[iid].type.value,
            "title": items[iid].title,
            "content": items[iid].content,
        }
        for iid in item_ids
        if iid in items
    ]
