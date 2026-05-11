import pytest
from app.query_engine.rls import inject_rls


class TestInjectRls:
    def test_superadmin_bypasses_rls(self):
        sql = "SELECT * FROM orders"
        result = inject_rls(sql, {"region": "华东"}, "superadmin")
        assert result == sql

    def test_empty_scopes_unchanged(self):
        sql = "SELECT * FROM orders"
        result = inject_rls(sql, {}, "viewer")
        assert result == sql

    def test_viewer_gets_filter_injected(self):
        sql = "SELECT * FROM orders"
        result = inject_rls(sql, {"region": "华东"}, "viewer")
        assert "华东" in result
        assert "_chatbi_rls" in result

    def test_analyst_gets_filter_injected_when_scopes_set(self):
        sql = "SELECT * FROM orders"
        result = inject_rls(sql, {"region": "华北"}, "analyst")
        assert "华北" in result

    def test_multiple_scopes_all_injected(self):
        sql = "SELECT * FROM orders"
        result = inject_rls(sql, {"region": "华东", "team": "Alpha"}, "viewer")
        assert "华东" in result
        assert "Alpha" in result
        assert "AND" in result

    def test_trailing_semicolon_stripped(self):
        sql = "SELECT * FROM orders;"
        result = inject_rls(sql, {"region": "华东"}, "viewer")
        assert result.count(";") <= 1

    def test_rls_wraps_as_subquery(self):
        sql = "SELECT id, sales FROM orders"
        result = inject_rls(sql, {"region": "华东"}, "viewer")
        assert "SELECT id, sales FROM orders" in result
        assert result.strip().upper().startswith("SELECT")

    def test_scope_values_are_escaped(self):
        result = inject_rls("SELECT * FROM orders", {"region": "O'Reilly"}, "viewer")
        assert "O''Reilly" in result

    def test_invalid_scope_key_rejected(self):
        with pytest.raises(ValueError):
            inject_rls("SELECT * FROM orders", {"region; DROP TABLE users": "x"}, "viewer")
