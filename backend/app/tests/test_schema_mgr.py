import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.models.user import User, UserRole
from app.models.datasource import Datasource, DBType
from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.core.security import hash_password, create_access_token
from app.core.encryption import encrypt

# Include the schema router in the test app (Task 6 will do this in the main router;
# for now we mount it here only if it hasn't been mounted already).
from app.main import app as _app
from app.schema_mgr.router import router as _schema_router

_already_included = any(
    hasattr(r, "path") and r.path.startswith("/api/v1/schema")
    for r in _app.routes
)
if not _already_included:
    _app.include_router(_schema_router, prefix="/api/v1")


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _create_admin_and_datasource(db_session):
    admin = User(
        email="schemadmin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    ds = Datasource(
        name="Test DB",
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


class TestSchemaTableCRUD:
    @pytest.mark.asyncio
    async def test_list_tables_returns_empty_for_new_datasource(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)
        resp = await client.get(
            f"/api/v1/schema/{ds.id}/tables",
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_tables_requires_admin(self, client: AsyncClient, db_session):
        admin, ds = await _create_admin_and_datasource(db_session)
        viewer = User(
            email="viewer2@example.com",
            hashed_password=hash_password("pass"),
            role=UserRole.viewer,
        )
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        resp = await client.get(
            f"/api/v1/schema/{ds.id}/tables",
            headers=auth_header(viewer.id, "viewer"),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_patch_table_updates_description(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)
        table = SchemaTable(
            datasource_id=ds.id,
            table_name="orders",
            description=None,
            is_active=True,
        )
        db_session.add(table)
        await db_session.commit()
        await db_session.refresh(table)

        resp = await client.patch(
            f"/api/v1/schema/tables/{table.id}",
            json={"description": "All customer orders"},
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "All customer orders"

    @pytest.mark.asyncio
    async def test_patch_table_returns_404_for_unknown(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)
        resp = await client.patch(
            "/api/v1/schema/tables/999999",
            json={"description": "x"},
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_columns_for_table(self, client: AsyncClient, db_session):
        admin, ds = await _create_admin_and_datasource(db_session)
        table = SchemaTable(
            datasource_id=ds.id, table_name="orders", is_active=True
        )
        db_session.add(table)
        await db_session.commit()
        await db_session.refresh(table)

        col = SchemaColumn(
            table_id=table.id,
            column_name="order_id",
            data_type="integer",
        )
        db_session.add(col)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/schema/tables/{table.id}/columns",
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["column_name"] == "order_id"

    @pytest.mark.asyncio
    async def test_patch_column_updates_description_and_examples(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)
        table = SchemaTable(
            datasource_id=ds.id, table_name="orders", is_active=True
        )
        db_session.add(table)
        await db_session.commit()
        await db_session.refresh(table)

        col = SchemaColumn(
            table_id=table.id, column_name="region", data_type="varchar"
        )
        db_session.add(col)
        await db_session.commit()
        await db_session.refresh(col)

        with patch("app.schema_mgr.router.embedding_service") as mock_embed_svc, \
             patch("app.schema_mgr.router.qdrant_store") as mock_qdrant:
            mock_embed_svc.embed.return_value = [[0.1] * 1024]
            mock_qdrant.ensure_collection = AsyncMock()
            mock_qdrant.upsert = AsyncMock()

            resp = await client.patch(
                f"/api/v1/schema/columns/{col.id}",
                json={
                    "description": "Geographic region",
                    "example_values": "华东, 华南, 华北",
                },
                headers=auth_header(admin.id, "admin"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Geographic region"
        assert data["example_values"] == "华东, 华南, 华北"

    @pytest.mark.asyncio
    async def test_patch_column_returns_404_for_unknown(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)
        resp = await client.patch(
            "/api/v1/schema/columns/999999",
            json={"description": "x"},
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 404
