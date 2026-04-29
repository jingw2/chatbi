from __future__ import annotations
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schema_column import SchemaColumn
from app.models.schema_table import SchemaTable
from app.embedding import embedding_service
from app.qdrant_store import qdrant_store

_SCHEMA_COLLECTION = "schema_columns"
_RETRIEVAL_CANDIDATE_COUNT = 20  # retrieve top-20 from Qdrant before reranking


async def retrieve_schema(
    query: str,
    datasource_id: int,
    db: AsyncSession,
    top_k: int = 5,
) -> list[dict]:
    """Return top-k schema columns most relevant to the query.

    Pipeline: embed query → Qdrant top-20 → bge-reranker top-k → fetch full records.

    Returns list of dicts with keys:
        table_name, column_name, data_type, description, example_values, notes

    Returns empty list if no embeddings exist for the datasource.
    """
    # 1. Embed the query (offloaded — FlagEmbedding is synchronous)
    query_vector = await asyncio.get_running_loop().run_in_executor(
        None, lambda: embedding_service.embed([query])[0]
    )

    # 2. Search Qdrant — top-20 candidates
    hits = await qdrant_store.search(
        _SCHEMA_COLLECTION,
        query_vector,
        top_k=_RETRIEVAL_CANDIDATE_COUNT,
        filter_={"datasource_id": datasource_id},
    )
    if not hits:
        return []

    # 3. Rerank — keep top-k
    passages = [
        f"{h['payload'].get('table_name', '')}.{h['payload'].get('column_name', '')}: "
        f"{h['payload'].get('description', '')}"
        for h in hits
    ]
    scores = await asyncio.get_running_loop().run_in_executor(
        None, lambda: embedding_service.rerank(query, passages)
    )
    ranked = sorted(zip(scores, hits), key=lambda x: x[0], reverse=True)[:top_k]
    top_column_ids = [int(item[1]["payload"]["column_id"]) for item in ranked]

    # 4. Fetch full column records from DB
    result_rows = await db.execute(
        select(SchemaColumn, SchemaTable)
        .join(SchemaTable, SchemaColumn.table_id == SchemaTable.id)
        .where(SchemaColumn.id.in_(top_column_ids))
    )
    rows = result_rows.all()

    # Return in ranked order
    col_map = {col.id: (col, tbl) for col, tbl in rows}
    return [
        {
            "table_name": col_map[cid][1].table_name,
            "column_name": col_map[cid][0].column_name,
            "data_type": col_map[cid][0].data_type,
            "description": col_map[cid][0].description,
            "example_values": col_map[cid][0].example_values,
            "notes": col_map[cid][0].notes,
        }
        for cid in top_column_ids
        if cid in col_map
    ]
