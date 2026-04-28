from __future__ import annotations
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PointIdsList,
)


class QdrantStore:
    """Async wrapper around qdrant-client for schema and knowledge embeddings.

    Two collections used:
      - "schema_columns": one point per schema column
      - "knowledge_items": one point per knowledge item

    Filter by datasource_id when searching to keep tenants isolated.
    """

    EMBEDDING_DIM = 1024  # BAAI/bge-m3 output dimension

    def __init__(self, url: str = "http://qdrant:6333"):
        self._client = AsyncQdrantClient(url=url)

    async def ensure_collection(self, name: str) -> None:
        """Create collection if it does not already exist."""
        response = await self._client.get_collections()
        existing = {c.name for c in response.collections}
        if name not in existing:
            try:
                await self._client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=self.EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )
            except Exception:
                # Collection may have been created by a concurrent worker — that's fine
                pass

    async def upsert(self, collection: str, points: list[dict]) -> None:
        """Upsert embedding points.

        Each point dict: {"id": str (UUID), "vector": list[float], "payload": dict}
        IDs must be valid UUID strings (e.g. str(uuid.uuid4())).
        """
        if not points:
            return
        qdrant_points = [
            PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points
        ]
        await self._client.upsert(
            collection_name=collection,
            points=qdrant_points,
        )

    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int = 20,
        filter_: dict | None = None,
    ) -> list[dict]:
        """Search by vector. Returns list of {id, score, payload} dicts."""
        qdrant_filter = None
        if filter_:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_.items()
                ]
            )
        results = await self._client.search(
            collection_name=collection,
            query_vector=vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [
            {"id": str(r.id), "score": r.score, "payload": r.payload}
            for r in results
        ]

    async def delete(self, collection: str, ids: list[str]) -> None:
        """Delete points by their UUID string IDs."""
        await self._client.delete(
            collection_name=collection,
            points_selector=PointIdsList(points=ids),
        )
