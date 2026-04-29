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


class TestSchemaSync:
    @pytest.mark.asyncio
    async def test_sync_creates_tables_and_columns(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)

        fake_schema = [
            {
                "table_name": "orders",
                "columns": [
                    {"column_name": "id", "data_type": "integer"},
                    {"column_name": "region", "data_type": "character varying"},
                ],
            }
        ]

        with patch("app.schema_mgr.router.introspect_postgres", new_callable=AsyncMock) as mock_introspect, \
             patch("app.schema_mgr.router.embedding_service") as mock_embed, \
             patch("app.schema_mgr.router.qdrant_store") as mock_qdrant:
            mock_introspect.return_value = fake_schema
            mock_embed.embed.return_value = [[0.1] * 1024, [0.2] * 1024]
            mock_qdrant.ensure_collection = AsyncMock()
            mock_qdrant.upsert = AsyncMock()

            resp = await client.post(
                f"/api/v1/schema/{ds.id}/sync",
                headers=auth_header(admin.id, "admin"),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tables_synced"] == 1
        assert data["columns_synced"] == 2
        assert data["embeddings_queued"] == 2

    @pytest.mark.asyncio
    async def test_sync_returns_404_for_unknown_datasource(
        self, client: AsyncClient, db_session
    ):
        admin, ds = await _create_admin_and_datasource(db_session)
        resp = await client.post(
            "/api/v1/schema/999999/sync",
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_sync_returns_400_for_non_postgres(
        self, client: AsyncClient, db_session
    ):
        from app.models.datasource import DBType
        from app.core.encryption import encrypt

        admin = User(
            email="syncadmin@example.com",
            hashed_password=hash_password("pass"),
            role=UserRole.admin,
        )
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        mysql_ds = Datasource(
            name="MySQL DB",
            db_type=DBType.mysql,
            host="localhost",
            port=3306,
            database="testdb",
            username="user",
            encrypted_password=encrypt("pass"),
            readonly_user="ro",
            readonly_encrypted_password=encrypt("ropass"),
            created_by=admin.id,
        )
        db_session.add(mysql_ds)
        await db_session.commit()
        await db_session.refresh(mysql_ds)

        resp = await client.post(
            f"/api/v1/schema/{mysql_ds.id}/sync",
            headers=auth_header(admin.id, "admin"),
        )
        assert resp.status_code == 400
        assert "PostgreSQL" in resp.json()["detail"]


class TestRetrieveSchema:
    @pytest.mark.asyncio
    async def test_retrieve_schema_returns_top_k_columns(self, db_session):
        from app.schema_mgr.retrieval import retrieve_schema
        from app.models.datasource import DBType
        from app.core.encryption import encrypt

        mock_embed_svc = MagicMock()
        mock_embed_svc.embed.return_value = [[0.5] * 1024]
        mock_embed_svc.rerank.return_value = [0.9, 0.7]

        mock_qdrant = MagicMock()

        admin = User(
            email="retradmin@example.com",
            hashed_password=hash_password("pass"),
            role=UserRole.admin,
        )
        db_session.add(admin)
        ds = Datasource(
            name="Ret DB", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=1,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        tbl = SchemaTable(datasource_id=ds.id, table_name="orders", is_active=True)
        db_session.add(tbl)
        await db_session.commit()
        await db_session.refresh(tbl)

        col1 = SchemaColumn(
            table_id=tbl.id, column_name="region",
            data_type="varchar", description="Region field",
            example_values="华东, 华南",
        )
        col2 = SchemaColumn(
            table_id=tbl.id, column_name="order_id",
            data_type="integer", description="Order ID",
        )
        db_session.add_all([col1, col2])
        await db_session.commit()
        await db_session.refresh(col1)
        await db_session.refresh(col2)

        mock_qdrant.search = AsyncMock(
            return_value=[
                {"id": f"uid-{col1.id}", "score": 0.9, "payload": {
                    "column_id": col1.id, "table_name": "orders",
                    "column_name": "region", "description": "Region field",
                }},
                {"id": f"uid-{col2.id}", "score": 0.7, "payload": {
                    "column_id": col2.id, "table_name": "orders",
                    "column_name": "order_id", "description": "Order ID",
                }},
            ]
        )

        with patch("app.schema_mgr.retrieval.embedding_service", mock_embed_svc), \
             patch("app.schema_mgr.retrieval.qdrant_store", mock_qdrant):
            results = await retrieve_schema(
                query="出库量按地区",
                datasource_id=ds.id,
                db=db_session,
                top_k=2,
            )

        assert len(results) == 2
        assert results[0]["column_name"] == "region"
        assert results[0]["example_values"] == "华东, 华南"

    @pytest.mark.asyncio
    async def test_retrieve_schema_returns_empty_when_no_embeddings(
        self, db_session
    ):
        from app.schema_mgr.retrieval import retrieve_schema

        mock_embed_svc = MagicMock()
        mock_embed_svc.embed.return_value = [[0.5] * 1024]

        mock_qdrant = MagicMock()
        mock_qdrant.search = AsyncMock(return_value=[])

        admin = User(
            email="emptyretr@example.com",
            hashed_password=hash_password("pass"),
            role=UserRole.admin,
        )
        db_session.add(admin)
        await db_session.commit()

        with patch("app.schema_mgr.retrieval.embedding_service", mock_embed_svc), \
             patch("app.schema_mgr.retrieval.qdrant_store", mock_qdrant):
            results = await retrieve_schema(
                query="anything", datasource_id=999, db=db_session
            )

        assert results == []
