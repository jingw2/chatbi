import pytest
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.models.datasource import Datasource, DBType
from app.models.workflow import Workflow
from app.core.security import hash_password, create_access_token
from app.core.encryption import encrypt

from app.main import app as _app
from app.workflow.router import router as _wf_router
_already_included = any(
    hasattr(r, "path") and "/workflows" in r.path
    for r in _app.routes
)
if not _already_included:
    _app.include_router(_wf_router, prefix="/api/v1")


def auth_header(user_id: int, role: str = "admin") -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _setup(db_session):
    admin = User(email="wfrouter@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    ds = Datasource(
        name="WF Router DB", db_type=DBType.postgres,
        host="h", port=5432, database="d",
        username="u", encrypted_password=encrypt("p"),
        readonly_user="r", readonly_encrypted_password=encrypt("rp"),
        created_by=admin.id,
    )
    db_session.add(ds)
    await db_session.commit()
    await db_session.refresh(ds)
    return admin, ds


class TestWorkflowCRUD:
    @pytest.mark.asyncio
    async def test_create_workflow(self, client: AsyncClient, db_session):
        admin, ds = await _setup(db_session)
        resp = await client.post(
            "/api/v1/workflows",
            json={
                "name": "月度报表",
                "datasource_id": ds.id,
                "trigger_keywords": ["月度报表", "monthly report"],
                "steps": [{"name": "总销售", "sql": "SELECT SUM(sales) FROM orders"}],
            },
            headers=auth_header(admin.id),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "月度报表"
        assert data["trigger_keywords"] == ["月度报表", "monthly report"]
        assert len(data["steps"]) == 1

    @pytest.mark.asyncio
    async def test_list_workflows(self, client: AsyncClient, db_session):
        admin, ds = await _setup(db_session)
        wf = Workflow(
            name="W1", datasource_id=ds.id,
            trigger_keywords=["w1"], steps=[{"name": "s", "sql": "SELECT 1"}],
            created_by=admin.id,
        )
        db_session.add(wf)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/workflows?datasource_id={ds.id}",
            headers=auth_header(admin.id),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_update_workflow(self, client: AsyncClient, db_session):
        admin, ds = await _setup(db_session)
        wf = Workflow(
            name="Old", datasource_id=ds.id,
            trigger_keywords=["old"], steps=[{"name": "s", "sql": "SELECT 1"}],
            created_by=admin.id,
        )
        db_session.add(wf)
        await db_session.commit()
        await db_session.refresh(wf)

        resp = await client.patch(
            f"/api/v1/workflows/{wf.id}",
            json={"name": "New", "is_active": False},
            headers=auth_header(admin.id),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"
        assert resp.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_workflow(self, client: AsyncClient, db_session):
        admin, ds = await _setup(db_session)
        wf = Workflow(
            name="Del", datasource_id=ds.id,
            trigger_keywords=["del"], steps=[],
            created_by=admin.id,
        )
        db_session.add(wf)
        await db_session.commit()
        await db_session.refresh(wf)

        resp = await client.delete(
            f"/api/v1/workflows/{wf.id}",
            headers=auth_header(admin.id),
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_workflow(self, client: AsyncClient, db_session):
        admin, ds = await _setup(db_session)
        viewer = User(email="wfviewer@example.com", hashed_password=hash_password("p"), role=UserRole.viewer)
        db_session.add(viewer)
        await db_session.commit()
        await db_session.refresh(viewer)

        resp = await client.post(
            "/api/v1/workflows",
            json={
                "name": "Nope", "datasource_id": ds.id,
                "trigger_keywords": ["nope"], "steps": [],
            },
            headers=auth_header(viewer.id, role="viewer"),
        )
        assert resp.status_code == 403
