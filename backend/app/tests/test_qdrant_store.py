import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from qdrant_client.models import PointIdsList


class TestQdrantStore:
    @pytest.mark.asyncio
    async def test_ensure_collection_creates_when_missing(self):
        with patch("app.qdrant_store.store.AsyncQdrantClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client
            mock_client.get_collections.return_value = MagicMock(collections=[])

            from app.qdrant_store.store import QdrantStore
            store = QdrantStore(url="http://qdrant:6333")
            await store.ensure_collection("schema_columns")

        mock_client.create_collection.assert_called_once()
        call_kwargs = mock_client.create_collection.call_args.kwargs
        assert call_kwargs["collection_name"] == "schema_columns"

    @pytest.mark.asyncio
    async def test_ensure_collection_skips_if_exists(self):
        with patch("app.qdrant_store.store.AsyncQdrantClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client
            existing = MagicMock()
            existing.name = "schema_columns"
            mock_client.get_collections.return_value = MagicMock(
                collections=[existing]
            )

            from app.qdrant_store.store import QdrantStore
            store = QdrantStore(url="http://qdrant:6333")
            await store.ensure_collection("schema_columns")

        mock_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_sends_point_structs(self):
        with patch("app.qdrant_store.store.AsyncQdrantClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            from app.qdrant_store.store import QdrantStore
            store = QdrantStore(url="http://qdrant:6333")
            points = [
                {"id": "uuid-1", "vector": [0.1] * 1024, "payload": {"col": "x"}},
                {"id": "uuid-2", "vector": [0.2] * 1024, "payload": {"col": "y"}},
            ]
            await store.upsert("schema_columns", points)

        mock_client.upsert.assert_called_once()
        call_kwargs = mock_client.upsert.call_args.kwargs
        assert call_kwargs["collection_name"] == "schema_columns"
        assert len(call_kwargs["points"]) == 2

    @pytest.mark.asyncio
    async def test_search_returns_id_score_payload_dicts(self):
        with patch("app.qdrant_store.store.AsyncQdrantClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            hit = MagicMock()
            hit.id = "uuid-1"
            hit.score = 0.95
            hit.payload = {"column_name": "region"}
            mock_client.search.return_value = [hit]

            from app.qdrant_store.store import QdrantStore
            store = QdrantStore(url="http://qdrant:6333")
            results = await store.search("schema_columns", [0.1] * 1024, top_k=5)

        assert results == [{"id": "uuid-1", "score": 0.95, "payload": {"column_name": "region"}}]

    @pytest.mark.asyncio
    async def test_search_passes_datasource_id_filter(self):
        with patch("app.qdrant_store.store.AsyncQdrantClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client
            mock_client.search.return_value = []

            from app.qdrant_store.store import QdrantStore
            store = QdrantStore(url="http://qdrant:6333")
            await store.search(
                "schema_columns", [0.1] * 1024, top_k=10,
                filter_={"datasource_id": 42}
            )

        call_kwargs = mock_client.search.call_args.kwargs
        query_filter = call_kwargs["query_filter"]
        assert query_filter is not None
        assert len(query_filter.must) == 1
        assert query_filter.must[0].key == "datasource_id"
        assert query_filter.must[0].match.value == 42

    @pytest.mark.asyncio
    async def test_delete_passes_ids_to_client(self):
        with patch("app.qdrant_store.store.AsyncQdrantClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            from app.qdrant_store.store import QdrantStore
            store = QdrantStore(url="http://qdrant:6333")
            await store.delete("knowledge_items", ["uuid-1", "uuid-2"])

        mock_client.delete.assert_called_once()
        call_kwargs = mock_client.delete.call_args.kwargs
        assert call_kwargs["collection_name"] == "knowledge_items"
        assert call_kwargs["points_selector"].points == ["uuid-1", "uuid-2"]
