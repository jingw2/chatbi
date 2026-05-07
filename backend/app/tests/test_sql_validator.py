import pytest
from app.query_engine.sql_validator import validate_sql


class TestValidateSql:
    def test_valid_select_passes(self):
        ok, msg = validate_sql(
            "SELECT id, region, sales FROM orders WHERE region = '华东'",
            {"orders"},
        )
        assert ok is True
        assert msg == ""

    def test_select_star_passes(self):
        ok, msg = validate_sql("SELECT * FROM orders LIMIT 10", {"orders"})
        assert ok is True

    def test_insert_rejected(self):
        ok, msg = validate_sql("INSERT INTO orders VALUES (1, '华东', 100)", {"orders"})
        assert ok is False
        assert "SELECT" in msg

    def test_update_rejected(self):
        ok, msg = validate_sql("UPDATE orders SET sales = 0", {"orders"})
        assert ok is False

    def test_delete_rejected(self):
        ok, msg = validate_sql("DELETE FROM orders WHERE id = 1", {"orders"})
        assert ok is False

    def test_drop_rejected(self):
        ok, msg = validate_sql("DROP TABLE orders", {"orders"})
        assert ok is False

    def test_table_not_in_whitelist_rejected(self):
        ok, msg = validate_sql("SELECT * FROM orders", {"users"})
        assert ok is False
        assert "orders" in msg.lower()

    def test_empty_whitelist_skips_table_check(self):
        ok, msg = validate_sql("SELECT * FROM orders", set())
        assert ok is True

    def test_information_schema_rejected(self):
        ok, msg = validate_sql(
            "SELECT * FROM information_schema.tables", {"orders"}
        )
        assert ok is False
        assert "information_schema" in msg.lower()

    def test_pg_catalog_rejected(self):
        ok, msg = validate_sql(
            "SELECT * FROM pg_catalog.pg_tables", {"orders"}
        )
        assert ok is False

    def test_sys_schema_rejected(self):
        ok, msg = validate_sql("SELECT * FROM sys.tables", {"orders"})
        assert ok is False

    def test_invalid_sql_rejected(self):
        ok, msg = validate_sql("NOT VALID SQL !!! @@@", {"orders"})
        assert ok is False

    def test_subquery_tables_checked(self):
        sql = "SELECT * FROM (SELECT id FROM secret_table) AS sub"
        ok, msg = validate_sql(sql, {"orders"})
        assert ok is False
        assert "secret_table" in msg.lower()
