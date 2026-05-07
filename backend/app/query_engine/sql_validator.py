from __future__ import annotations

import sqlglot
import sqlglot.expressions as exp

_BLOCKED_SCHEMAS = {"information_schema", "pg_catalog", "sys", "mysql", "performance_schema"}


def validate_sql(sql: str, allowed_tables: set[str]) -> tuple[bool, str]:
    """Validate SQL for safety and table whitelist compliance.

    Checks:
    1. Must be a single SELECT statement (no INSERT, UPDATE, DELETE, DDL).
    2. No access to system schemas (information_schema, pg_catalog, sys, etc.).
    3. All referenced tables must be in allowed_tables (skipped if set is empty).

    Returns: (is_valid, error_message)
    """
    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except Exception as exc:
        return False, f"SQL parse error: {exc}"

    if not statements or statements[0] is None:
        return False, "Empty or unparseable SQL"

    stmt = statements[0]

    # Must be SELECT
    if not isinstance(stmt, exp.Select):
        stmt_type = type(stmt).__name__
        return False, f"Only SELECT statements are allowed, got: {stmt_type}"

    # Check all referenced tables
    allowed_lower = {t.lower() for t in allowed_tables}
    for table in stmt.find_all(exp.Table):
        # Check schema (db qualifier)
        db_expr = table.args.get("db")
        if db_expr is not None:
            schema_name = db_expr.name.lower()
            if schema_name in _BLOCKED_SCHEMAS:
                return False, f"Access to system schema not allowed: {schema_name}"

        # Check table name against whitelist (only if whitelist is non-empty)
        if allowed_lower:
            table_name = table.name.lower()
            if table_name not in allowed_lower:
                return False, f"Table '{table_name}' is not in the allowed tables for this datasource"

    return True, ""
