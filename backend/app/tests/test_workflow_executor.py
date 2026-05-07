import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.workflow.executor import run_workflow, WorkflowResult


class TestRunWorkflow:
    def _make_workflow(self, steps):
        wf = MagicMock()
        wf.id = 1
        wf.name = "月度报表"
        wf.steps = steps
        return wf

    def _make_datasource(self):
        ds = MagicMock()
        ds.host = "localhost"
        ds.port = 5432
        ds.database = "testdb"
        ds.readonly_user = "ro"
        ds.readonly_encrypted_password = "encrypted"
        return ds

    @pytest.mark.asyncio
    async def test_single_step_returns_result(self):
        wf = self._make_workflow([
            {"name": "总销售额", "sql": "SELECT SUM(sales) AS total FROM orders"},
        ])
        ds = self._make_datasource()

        with patch("app.workflow.executor.execute_query", new_callable=AsyncMock) as mock_exec, \
             patch("app.workflow.executor.decrypt", return_value="plain"):
            mock_exec.return_value = {
                "columns": ["total"],
                "rows": [[50000]],
                "execution_ms": 10,
            }
            result = await run_workflow(wf, ds)

        assert isinstance(result, WorkflowResult)
        assert len(result.step_results) == 1
        assert result.step_results[0]["name"] == "总销售额"
        assert result.step_results[0]["columns"] == ["total"]
        assert result.step_results[0]["rows"] == [[50000]]
        assert result.error is None

    @pytest.mark.asyncio
    async def test_multi_step_returns_all_results(self):
        wf = self._make_workflow([
            {"name": "华东销售", "sql": "SELECT SUM(sales) FROM orders WHERE region='华东'"},
            {"name": "华南销售", "sql": "SELECT SUM(sales) FROM orders WHERE region='华南'"},
        ])
        ds = self._make_datasource()

        call_count = 0
        async def mock_exec(**kwargs):
            nonlocal call_count
            call_count += 1
            return {
                "columns": ["total"],
                "rows": [[1000 * call_count]],
                "execution_ms": 5,
            }

        with patch("app.workflow.executor.execute_query", side_effect=mock_exec), \
             patch("app.workflow.executor.decrypt", return_value="plain"):
            result = await run_workflow(wf, ds)

        assert len(result.step_results) == 2
        assert result.step_results[0]["name"] == "华东销售"
        assert result.step_results[1]["name"] == "华南销售"
        assert result.total_execution_ms > 0

    @pytest.mark.asyncio
    async def test_step_failure_records_error_and_continues(self):
        wf = self._make_workflow([
            {"name": "good_step", "sql": "SELECT 1"},
            {"name": "bad_step", "sql": "INVALID SQL"},
            {"name": "after_bad", "sql": "SELECT 2"},
        ])
        ds = self._make_datasource()

        call_idx = 0
        async def mock_exec(**kwargs):
            nonlocal call_idx
            call_idx += 1
            if call_idx == 2:
                raise Exception("syntax error")
            return {"columns": ["v"], "rows": [[call_idx]], "execution_ms": 1}

        with patch("app.workflow.executor.execute_query", side_effect=mock_exec), \
             patch("app.workflow.executor.decrypt", return_value="plain"):
            result = await run_workflow(wf, ds)

        assert len(result.step_results) == 3
        assert result.step_results[0]["error"] is None
        assert "syntax error" in result.step_results[1]["error"]
        assert result.step_results[2]["error"] is None

    @pytest.mark.asyncio
    async def test_empty_steps_returns_empty(self):
        wf = self._make_workflow([])
        ds = self._make_datasource()

        with patch("app.workflow.executor.decrypt", return_value="plain"):
            result = await run_workflow(wf, ds)

        assert result.step_results == []
        assert result.error is None

    @pytest.mark.asyncio
    async def test_result_has_workflow_name(self):
        wf = self._make_workflow([{"name": "s1", "sql": "SELECT 1"}])
        ds = self._make_datasource()

        with patch("app.workflow.executor.execute_query", new_callable=AsyncMock) as mock_exec, \
             patch("app.workflow.executor.decrypt", return_value="plain"):
            mock_exec.return_value = {"columns": ["v"], "rows": [[1]], "execution_ms": 1}
            result = await run_workflow(wf, ds)

        assert result.workflow_name == "月度报表"
