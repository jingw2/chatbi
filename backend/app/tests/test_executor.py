import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock


class TestExecuteQuery:
    def _make_record(self, keys: list[str], values: list):
        """Create a mock asyncpg Record."""
        record = MagicMock()
        record.keys.return_value = keys
        record.__iter__ = Mock(return_value=iter(values))
        return record

    @pytest.mark.asyncio
    async def test_returns_columns_and_rows(self):
        record = self._make_record(["region", "sales"], ["华东", 1000])
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[record])

        with patch("app.query_engine.executor.asyncpg.connect", return_value=mock_conn):
            from app.query_engine.executor import execute_query
            result = await execute_query(
                host="localhost", port=5432, database="db",
                username="user", password="pass",
                sql="SELECT region, sales FROM orders",
            )

        assert result["columns"] == ["region", "sales"]
        assert result["rows"] == [["华东", 1000]]
        assert isinstance(result["execution_ms"], int)
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_columns(self):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        with patch("app.query_engine.executor.asyncpg.connect", return_value=mock_conn):
            from app.query_engine.executor import execute_query
            result = await execute_query(
                host="h", port=5432, database="d",
                username="u", password="p", sql="SELECT * FROM orders",
            )

        assert result["columns"] == []
        assert result["rows"] == []

    @pytest.mark.asyncio
    async def test_limit_injected_when_missing(self):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        captured_sql = []

        async def capture_fetch(sql, *args, **kwargs):
            captured_sql.append(sql)
            return []

        mock_conn.fetch = capture_fetch

        with patch("app.query_engine.executor.asyncpg.connect", return_value=mock_conn):
            from app.query_engine.executor import execute_query
            await execute_query(
                host="h", port=5432, database="d",
                username="u", password="p",
                sql="SELECT * FROM orders",
            )

        assert "LIMIT" in captured_sql[0].upper()
        assert "10000" in captured_sql[0]

    @pytest.mark.asyncio
    async def test_existing_limit_preserved(self):
        mock_conn = AsyncMock()
        captured_sql = []

        async def capture_fetch(sql, *args, **kwargs):
            captured_sql.append(sql)
            return []

        mock_conn.fetch = capture_fetch

        with patch("app.query_engine.executor.asyncpg.connect", return_value=mock_conn):
            from app.query_engine.executor import execute_query
            await execute_query(
                host="h", port=5432, database="d",
                username="u", password="p",
                sql="SELECT * FROM orders LIMIT 5",
            )

        assert "LIMIT 5" in captured_sql[0]

    @pytest.mark.asyncio
    async def test_connection_closed_on_exception(self):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("DB error"))

        with patch("app.query_engine.executor.asyncpg.connect", return_value=mock_conn):
            from app.query_engine.executor import execute_query
            with pytest.raises(Exception, match="DB error"):
                await execute_query(
                    host="h", port=5432, database="d",
                    username="u", password="p", sql="SELECT 1",
                )

        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsupported_db_type_raises(self):
        from app.query_engine.executor import execute_query
        with pytest.raises(NotImplementedError, match="mysql"):
            await execute_query(
                host="h", port=3306, database="d",
                username="u", password="p",
                sql="SELECT 1", db_type="mysql",
            )
