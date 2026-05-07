import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.workflow.matcher import match_workflow


class TestMatchWorkflow:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_workflows(self, db_session):
        result = await match_workflow("华东区出库量", datasource_id=999, db=db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_matches_exact_keyword(self, db_session):
        from app.models.workflow import Workflow
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.core.security import hash_password
        from app.core.encryption import encrypt

        admin = User(email="wfmatch@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="WF DB", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=admin.id,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        wf = Workflow(
            name="月度报表", datasource_id=ds.id,
            trigger_keywords=["月度报表", "monthly report"],
            steps=[{"name": "step1", "sql": "SELECT 1"}],
            created_by=admin.id, is_active=True,
        )
        db_session.add(wf)
        await db_session.commit()
        await db_session.refresh(wf)

        result = await match_workflow("生成月度报表", datasource_id=ds.id, db=db_session)
        assert result is not None
        assert result.id == wf.id

    @pytest.mark.asyncio
    async def test_no_match_returns_none(self, db_session):
        from app.models.workflow import Workflow
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.core.security import hash_password
        from app.core.encryption import encrypt

        admin = User(email="wfnomatch@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="WF DB2", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=admin.id,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        wf = Workflow(
            name="月度报表", datasource_id=ds.id,
            trigger_keywords=["月度报表"],
            steps=[{"name": "step1", "sql": "SELECT 1"}],
            created_by=admin.id, is_active=True,
        )
        db_session.add(wf)
        await db_session.commit()

        result = await match_workflow("华东区出库量", datasource_id=ds.id, db=db_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_inactive_workflow_not_matched(self, db_session):
        from app.models.workflow import Workflow
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.core.security import hash_password
        from app.core.encryption import encrypt

        admin = User(email="wfinactive@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="WF DB3", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=admin.id,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        wf = Workflow(
            name="月度报表", datasource_id=ds.id,
            trigger_keywords=["月度报表"],
            steps=[{"name": "step1", "sql": "SELECT 1"}],
            created_by=admin.id, is_active=False,
        )
        db_session.add(wf)
        await db_session.commit()

        result = await match_workflow("月度报表", datasource_id=ds.id, db=db_session)
        assert result is None
