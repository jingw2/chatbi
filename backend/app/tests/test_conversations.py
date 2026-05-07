import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.models.user import User, UserRole
from app.models.datasource import Datasource, DBType
from app.models.conversation import Conversation
from app.models.query_log import QueryLog
from app.core.security import hash_password, create_access_token
from app.core.encryption import encrypt

# Mount router for tests (Task 6 registers it in main router)
from app.main import app as _app
from app.api.v1.conversations import router as _conv_router
_already_included = any(
    hasattr(r, "path") and "/conversations" in r.path
    for r in _app.routes
)
if not _already_included:
    _app.include_router(_conv_router, prefix="/api/v1")


def auth_header(user_id: int, role: str = "viewer") -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _setup(db_session):
    user = User(email="convtest@example.com", hashed_password=hash_password("p"), role=UserRole.viewer)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    ds = Datasource(
        name="Conv DB", db_type=DBType.postgres,
        host="h", port=5432, database="d",
        username="u", encrypted_password=encrypt("p"),
        readonly_user="r", readonly_encrypted_password=encrypt("rp"),
        created_by=user.id,
    )
    db_session.add(ds)
    await db_session.commit()
    await db_session.refresh(ds)
    return user, ds


class TestConversationsCRUD:
    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient, db_session):
        user, ds = await _setup(db_session)
        resp = await client.post(
            "/api/v1/conversations",
            json={"datasource_id": ds.id, "title": "My first chat"},
            headers=auth_header(user.id),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My first chat"
        assert data["user_id"] == user.id

    @pytest.mark.asyncio
    async def test_list_conversations_only_own(self, client: AsyncClient, db_session):
        user, ds = await _setup(db_session)
        conv = Conversation(user_id=user.id, datasource_id=ds.id, title="Chat 1")
        db_session.add(conv)
        await db_session.commit()

        resp = await client.get("/api/v1/conversations", headers=auth_header(user.id))
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Chat 1"

    @pytest.mark.asyncio
    async def test_rename_conversation(self, client: AsyncClient, db_session):
        user, ds = await _setup(db_session)
        conv = Conversation(user_id=user.id, datasource_id=ds.id, title="Old title")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        resp = await client.patch(
            f"/api/v1/conversations/{conv.id}",
            json={"title": "New title"},
            headers=auth_header(user.id),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New title"

    @pytest.mark.asyncio
    async def test_rename_other_users_conversation_returns_404(
        self, client: AsyncClient, db_session
    ):
        user, ds = await _setup(db_session)
        other = User(email="other@example.com", hashed_password=hash_password("p"), role=UserRole.viewer)
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        conv = Conversation(user_id=other.id, datasource_id=ds.id, title="Other chat")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        resp = await client.patch(
            f"/api/v1/conversations/{conv.id}",
            json={"title": "Hijacked"},
            headers=auth_header(user.id),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation(self, client: AsyncClient, db_session):
        user, ds = await _setup(db_session)
        conv = Conversation(user_id=user.id, datasource_id=ds.id, title="To delete")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        resp = await client.delete(
            f"/api/v1/conversations/{conv.id}",
            headers=auth_header(user.id),
        )
        assert resp.status_code == 204


class TestChatQuery:
    @pytest.mark.asyncio
    async def test_query_returns_result_and_logs_to_db(
        self, client: AsyncClient, db_session
    ):
        user, ds = await _setup(db_session)
        conv = Conversation(user_id=user.id, datasource_id=ds.id, title="New chat")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        from app.query_engine.pipeline import PipelineResult

        fake_result = PipelineResult(
            intent="data_query",
            sql="SELECT region, SUM(qty) FROM orders GROUP BY 1",
            columns=["region", "qty"],
            rows=[["华东", 5000]],
            chart_type="bar",
            insight="华东区出库量最高。",
            suggestions=["加大华东区库存", "优化华南区供应链"],
            error=None,
            execution_ms=42,
            warnings=[],
        )

        with patch("app.api.v1.conversations.run_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = fake_result

            resp = await client.post(
                f"/api/v1/conversations/{conv.id}/query",
                json={"question": "各地区出库量"},
                headers=auth_header(user.id),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "data_query"
        assert data["sql"] == "SELECT region, SUM(qty) FROM orders GROUP BY 1"
        assert data["chart_type"] == "bar"
        assert data["insight"] == "华东区出库量最高。"
        assert len(data["suggestions"]) == 2
        assert data["query_log_id"] is not None

    @pytest.mark.asyncio
    async def test_query_on_other_users_conversation_returns_403(
        self, client: AsyncClient, db_session
    ):
        user, ds = await _setup(db_session)
        other = User(email="other2@example.com", hashed_password=hash_password("p"), role=UserRole.viewer)
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)

        conv = Conversation(user_id=other.id, datasource_id=ds.id, title="Other conv")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        resp = await client.post(
            f"/api/v1/conversations/{conv.id}/query",
            json={"question": "data"},
            headers=auth_header(user.id),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_query_auto_titles_conversation(
        self, client: AsyncClient, db_session
    ):
        """First query sets conversation title to first 30 chars of question."""
        user, ds = await _setup(db_session)
        conv = Conversation(user_id=user.id, datasource_id=ds.id, title="New chat")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        from app.query_engine.pipeline import PipelineResult

        fake_result = PipelineResult(
            intent="chitchat", sql=None, columns=[], rows=[],
            chart_type=None, insight=None, suggestions=[],
            error=None, execution_ms=None, warnings=[],
        )

        question = "这是一个很长的问题，用来测试自动标题功能，超过三十个字符"
        with patch("app.api.v1.conversations.run_pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = fake_result
            await client.post(
                f"/api/v1/conversations/{conv.id}/query",
                json={"question": question},
                headers=auth_header(user.id),
            )

        # Reload conversation from DB
        from sqlalchemy import select as sa_select
        result = await db_session.execute(
            sa_select(Conversation).where(Conversation.id == conv.id)
        )
        updated_conv = result.scalar_one()
        assert updated_conv.title == question[:30]
