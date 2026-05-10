from __future__ import annotations

import asyncio
import time

import asyncpg

_MAX_ROWS = 10000
_DEFAULT_TIMEOUT = 30.0


def _enforce_limit(sql: str, max_rows: int = _MAX_ROWS) -> str:
    """Append LIMIT clause if not already present."""
    if "limit" not in sql.lower():
        return f"{sql.rstrip(';').rstrip()} LIMIT {max_rows}"
    return sql


async def execute_query(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    sql: str,
    timeout: float = _DEFAULT_TIMEOUT,
    db_type: str = "postgres",
    read_only: bool = False,
) -> dict:
    """Execute a SQL query and return columns + rows.

    Only PostgreSQL is supported in this version.

    Args:
        read_only: If True, execute within a READ ONLY transaction to
            prevent any INSERT/UPDATE/DELETE/DDL from succeeding.

    Returns:
        {"columns": list[str], "rows": list[list], "execution_ms": int}

    Raises:
        NotImplementedError: for non-postgres db_type
        asyncpg.PostgresError: on DB-level errors
        asyncio.TimeoutError: if query exceeds timeout
    """
    if db_type != "postgres":
        raise NotImplementedError(
            f"Query execution for '{db_type}' is not supported in this version."
        )

    sql = _enforce_limit(sql)

    conn = await asyncpg.connect(
        host=host, port=port, database=database,
        user=username, password=password,
    )
    start = time.monotonic()
    try:
        if read_only:
            # Wrap in a read-only transaction — any write attempt raises
            async with conn.transaction(readonly=True):
                rows = await asyncio.wait_for(conn.fetch(sql), timeout=timeout)
        else:
            rows = await asyncio.wait_for(conn.fetch(sql), timeout=timeout)
        execution_ms = int((time.monotonic() - start) * 1000)
        columns = list(rows[0].keys()) if rows else []
        return {
            "columns": columns,
            "rows": [list(r) for r in rows],
            "execution_ms": execution_ms,
        }
    finally:
        await conn.close()
