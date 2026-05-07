import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass


class TestRunPipeline:
    def _mock_user(self, role="viewer"):
        user = MagicMock()
        user.id = 1
        user.role.value = role
        return user

    def _mock_datasource(self):
        ds = MagicMock()
        ds.id = 1
        ds.host = "localhost"
        ds.port = 5432
        ds.database = "testdb"
        ds.readonly_user = "ro"
        ds.readonly_encrypted_password = "encrypted"
        return ds

    @pytest.mark.asyncio
    async def test_non_data_query_intent_returns_early(self, db_session):
        from app.query_engine.pipeline import run_pipeline

        with patch("app.query_engine.pipeline.llm_gateway") as mock_gw:
            mock_gw.intent = AsyncMock(return_value="chitchat")

            result = await run_pipeline(
                question="你好", datasource_id=1,
                user=self._mock_user(), db=db_session,
            )

        assert result.intent == "chitchat"
        assert result.sql is None
        assert result.rows == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_datasource_not_found_returns_error(self, db_session):
        from app.query_engine.pipeline import run_pipeline

        with patch("app.query_engine.pipeline.llm_gateway") as mock_gw:
            mock_gw.intent = AsyncMock(return_value="data_query")
            result = await run_pipeline(
                question="出库量", datasource_id=999999,
                user=self._mock_user(), db=db_session,
            )

        assert result.intent == "data_query"
        assert result.error is not None
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_sql_validation_failure_exhausts_retries(self, db_session):
        from app.query_engine.pipeline import run_pipeline
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.core.security import hash_password
        from app.core.encryption import encrypt

        admin = User(email="pipe1@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="Pipe DB", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=admin.id,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        with patch("app.query_engine.pipeline.llm_gateway") as mock_gw, \
             patch("app.query_engine.pipeline.retrieve_schema", new_callable=AsyncMock) as mock_schema, \
             patch("app.query_engine.pipeline.retrieve_knowledge", new_callable=AsyncMock) as mock_knowledge:
            mock_gw.intent = AsyncMock(return_value="data_query")
            mock_gw.text_to_sql = AsyncMock(return_value="DROP TABLE orders")  # always invalid
            mock_schema.return_value = []
            mock_knowledge.return_value = []

            result = await run_pipeline(
                question="出库量", datasource_id=ds.id,
                user=self._mock_user(), db=db_session,
                max_sql_retries=2,
            )

        assert result.sql is None
        assert result.error is not None
        assert "validation" in result.error.lower() or "SELECT" in result.error

    @pytest.mark.asyncio
    async def test_successful_pipeline_returns_full_result(self, db_session):
        from app.query_engine.pipeline import run_pipeline
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.core.security import hash_password
        from app.core.encryption import encrypt

        admin = User(email="pipe2@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="Pipe DB 2", db_type=DBType.postgres,
            host="h", port=5432, database="d",
            username="u", encrypted_password=encrypt("p"),
            readonly_user="r", readonly_encrypted_password=encrypt("rp"),
            created_by=admin.id,
        )
        db_session.add(ds)
        await db_session.commit()
        await db_session.refresh(ds)

        with patch("app.query_engine.pipeline.llm_gateway") as mock_gw, \
             patch("app.query_engine.pipeline.retrieve_schema", new_callable=AsyncMock) as mock_schema, \
             patch("app.query_engine.pipeline.retrieve_knowledge", new_callable=AsyncMock) as mock_knowledge, \
             patch("app.query_engine.pipeline.execute_query", new_callable=AsyncMock) as mock_exec, \
             patch("app.query_engine.pipeline.decrypt", return_value="plain_pass"):
            mock_gw.intent = AsyncMock(return_value="data_query")
            mock_gw.text_to_sql = AsyncMock(return_value="SELECT region, SUM(qty) FROM orders GROUP BY 1")
            mock_gw.base = AsyncMock(return_value="INSIGHT: Sales are up.\nSUGGESTION: Focus on 华东.")
            mock_schema.return_value = [
                {"table_name": "orders", "column_name": "region", "data_type": "varchar",
                 "description": None, "example_values": None, "notes": None}
            ]
            mock_knowledge.return_value = []
            mock_exec.return_value = {
                "columns": ["region", "total_qty"],
                "rows": [["华东", 5000], ["华南", 3000]],
                "execution_ms": 42,
            }

            result = await run_pipeline(
                question="各地区出库量", datasource_id=ds.id,
                user=self._mock_user(role="superadmin"), db=db_session,
            )

        assert result.intent == "data_query"
        assert result.sql is not None
        assert result.columns == ["region", "total_qty"]
        assert len(result.rows) == 2
        assert result.chart_type is not None
        assert result.chart_config is not None
        assert result.insight is not None
        assert result.error is None
        assert result.execution_ms == 42

    @pytest.mark.asyncio
    async def test_fixed_workflow_intent_runs_workflow(self, db_session):
        from app.query_engine.pipeline import run_pipeline
        from app.models.user import User, UserRole
        from app.models.datasource import Datasource, DBType
        from app.models.workflow import Workflow
        from app.core.security import hash_password
        from app.core.encryption import encrypt
        from app.workflow.executor import WorkflowResult

        admin = User(email="pipewf@example.com", hashed_password=hash_password("p"), role=UserRole.admin)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)

        ds = Datasource(
            name="Pipe WF DB", db_type=DBType.postgres,
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
            steps=[{"name": "总销售", "sql": "SELECT SUM(sales) FROM orders"}],
            created_by=admin.id, is_active=True,
        )
        db_session.add(wf)
        await db_session.commit()
        await db_session.refresh(wf)

        fake_wf_result = WorkflowResult(
            workflow_name="月度报表",
            step_results=[{
                "name": "总销售",
                "columns": ["total"],
                "rows": [[50000]],
                "execution_ms": 10,
                "error": None,
            }],
            total_execution_ms=10,
            error=None,
        )

        with patch("app.query_engine.pipeline.llm_gateway") as mock_gw, \
             patch("app.query_engine.pipeline.run_workflow", new_callable=AsyncMock) as mock_run_wf:
            mock_gw.intent = AsyncMock(return_value="fixed_workflow")
            mock_run_wf.return_value = fake_wf_result

            result = await run_pipeline(
                question="生成月度报表", datasource_id=ds.id,
                user=self._mock_user(), db=db_session,
            )

        assert result.intent == "fixed_workflow"
        assert result.workflow_result is not None
        assert result.workflow_result.workflow_name == "月度报表"
        assert len(result.workflow_result.step_results) == 1
        assert result.error is None

    @pytest.mark.asyncio
    async def test_fixed_workflow_intent_no_match_returns_error(self, db_session):
        from app.query_engine.pipeline import run_pipeline

        with patch("app.query_engine.pipeline.llm_gateway") as mock_gw:
            mock_gw.intent = AsyncMock(return_value="fixed_workflow")

            result = await run_pipeline(
                question="nonexistent workflow", datasource_id=999999,
                user=self._mock_user(), db=db_session,
            )

        assert result.intent == "fixed_workflow"
        assert result.workflow_result is None
        assert result.error is not None
