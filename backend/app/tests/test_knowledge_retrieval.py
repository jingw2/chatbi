import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRetrieveKnowledge:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_qdrant_hits(self, db_session):
        from app.query_engine.knowledge_retrieval import retrieve_knowledge

        mock_embed = MagicMock()
        mock_embed.embed.return_value = [[0.5] * 1024]
        mock_qdrant = MagicMock()
        mock_qdrant.search = AsyncMock(return_value=[])

        with patch("app.query_engine.knowledge_retrieval.embedding_service", mock_embed), \
             patch("app.query_engine.knowledge_retrieval.qdrant_store", mock_qdrant):
            result = await retrieve_knowledge(
                query="华东区出库量", datasource_id=999, db=db_session
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_ranked_knowledge_items(self, db_session):
        from app.query_engine.knowledge_retrieval import retrieve_knowledge
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.models.knowledge_item import KnowledgeItem, KnowledgeType
        from app.core.security import hash_password
        from app.core.encryption import encrypt

        # Seed DB
        admin = User(email="krtest@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="KR DB", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=admin.id,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        item1 = KnowledgeItem(
            datasource_id=ds.id, type=KnowledgeType.rule,
            title="华东区规则", content="华东区包括上海、江苏、浙江",
            embedding_id="uid-1", created_by=admin.id,
        )
        item2 = KnowledgeItem(
            datasource_id=ds.id, type=KnowledgeType.fewshot,
            title="出库量示例", content="SELECT region, SUM(qty) FROM orders GROUP BY 1",
            embedding_id="uid-2", created_by=admin.id,
        )
        db_session.add_all([item1, item2])
        await db_session.commit()
        await db_session.refresh(item1)
        await db_session.refresh(item2)

        mock_embed = MagicMock()
        mock_embed.embed.return_value = [[0.5] * 1024]
        mock_embed.rerank.return_value = [0.9, 0.7]

        mock_qdrant = MagicMock()
        mock_qdrant.search = AsyncMock(return_value=[
            {"id": "uid-1", "score": 0.9, "payload": {
                "item_id": item1.id, "datasource_id": ds.id,
                "type": "rule", "title": "华东区规则",
            }},
            {"id": "uid-2", "score": 0.7, "payload": {
                "item_id": item2.id, "datasource_id": ds.id,
                "type": "fewshot", "title": "出库量示例",
            }},
        ])

        with patch("app.query_engine.knowledge_retrieval.embedding_service", mock_embed), \
             patch("app.query_engine.knowledge_retrieval.qdrant_store", mock_qdrant):
            result = await retrieve_knowledge(
                query="华东区出库量", datasource_id=ds.id, db=db_session, top_k=2,
            )

        assert len(result) == 2
        assert result[0]["type"] == "rule"
        assert result[0]["content"] == "华东区包括上海、江苏、浙江"
        assert result[1]["type"] == "fewshot"
