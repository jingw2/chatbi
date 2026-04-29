import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.models.user import User, UserRole
from app.models.datasource import Datasource, DBType
from app.models.knowledge_item import KnowledgeItem, KnowledgeType
from app.core.security import hash_password, create_access_token
from app.core.encryption import encrypt

# Include the knowledge router in the test app (Task 6 will do this in the main router)
from app.main import app as _app
from app.knowledge.router import router as _knowledge_router

_already_included = any(
    hasattr(r, "path") and r.path.startswith("/api/v1/knowledge")
    for r in _app.routes
)
if not _already_included:
    _app.include_router(_knowledge_router, prefix="/api/v1")


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _setup(db_session):
    admin = User(
        email="kbadmin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    ds = Datasource(
        name="KB DB",
        db_type=DBType.postgres,
        host="localhost",
        port=5432,
        database="testdb",
        username="user",
        encrypted_password=encrypt("pass"),
        readonly_user="ro",
        readonly_encrypted_password=encrypt("ropass"),
        created_by=admin.id,
    )
    db_session.add(ds)
    await db_session.commit()
    await db_session.refresh(ds)
    return admin, ds


class TestKnowledgeCRUD:
    @pytest.mark.asyncio
    async def test_list_knowledge_items(self, client: AsyncClient, db_session):
        admin, ds = await _setup(db_session)
        item = KnowledgeItem(
            datasource_id=ds.id,
            type=KnowledgeType.rule,
            title="Rule 1",
            content="Always filter by region",
            created_by=admin.id,
        )
        db_session.add(item)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/knowledge?datasource_id={ds.id}",
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Rule 1"

    @pytest.mark.asyncio
    async def test_create_knowledge_item_embeds_and_stores(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _setup(db_session)

        with patch("app.knowledge.router.embedding_service") as mock_embed, \
             patch("app.knowledge.router.qdrant_store") as mock_qdrant:
            mock_embed.embed.return_value = [[0.3] * 1024]
            mock_qdrant.ensure_collection = AsyncMock()
            mock_qdrant.upsert = AsyncMock()

            resp = await client.post(
                "/api/v1/knowledge",
                json={
                    "datasource_id": ds.id,
                    "type": "glossary",
                    "title": "华东区",
                    "content": "East China region, includes Shanghai and Jiangsu",
                },
                headers=auth_header(admin.id, "admin"),
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "华东区"
        assert data["embedding_id"] is not None
        mock_qdrant.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_knowledge_item_reembeds(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _setup(db_session)
        item = KnowledgeItem(
            datasource_id=ds.id,
            type=KnowledgeType.fewshot,
            title="Q: top region",
            content="SELECT region, SUM(qty) FROM orders GROUP BY 1",
            embedding_id="existing-uuid",
            created_by=admin.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        with patch("app.knowledge.router.embedding_service") as mock_embed, \
             patch("app.knowledge.router.qdrant_store") as mock_qdrant:
            mock_embed.embed.return_value = [[0.4] * 1024]
            mock_qdrant.ensure_collection = AsyncMock()
            mock_qdrant.upsert = AsyncMock()

            resp = await client.patch(
                f"/api/v1/knowledge/{item.id}",
                json={"content": "SELECT region, COUNT(*) FROM orders GROUP BY 1"},
                headers=auth_header(admin.id, "admin"),
            )

        assert resp.status_code == 200
        assert "COUNT" in resp.json()["content"]
        mock_qdrant.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_knowledge_item_removes_from_qdrant(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _setup(db_session)
        item = KnowledgeItem(
            datasource_id=ds.id,
            type=KnowledgeType.rule,
            title="Old rule",
            content="Deprecated",
            embedding_id="del-uuid",
            created_by=admin.id,
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        with patch("app.knowledge.router.qdrant_store") as mock_qdrant:
            mock_qdrant.delete = AsyncMock()

            resp = await client.delete(
                f"/api/v1/knowledge/{item.id}",
                headers=auth_header(admin.id, "admin"),
            )

        assert resp.status_code == 204
        mock_qdrant.delete.assert_called_once_with("knowledge_items", ["del-uuid"])

    @pytest.mark.asyncio
    async def test_delete_knowledge_item_returns_404_for_unknown(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _setup(db_session)
        resp = await client.delete(
            "/api/v1/knowledge/999999",
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 404
