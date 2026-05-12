from __future__ import annotations

import asyncio
import time

import asyncpg
import aiosqlite

_MAX_ROWS = 10000
_DEFAULT_TIMEOUT = 30.0


def _enforce_limit(sql: str, max_rows: int = _MAX_ROWS) -> str:
    """Append LIMIT clause if not already present."""
    if "limit" not in sql.lower():
        return f"{sql.rstrip(';').rstrip()} LIMIT {max_rows}"
    return sql


async def _execute_postgres(
    host: str, port: int, database: str, username: str, password: str,
    sql: str, timeout: float, read_only: bool,
) -> dict:
    conn = await asyncpg.connect(
        host=host, port=port, database=database, user=username, password=password,
    )
    start = time.monotonic()
    try:
        if read_only:
            async with conn.transaction(readonly=True):
                rows = await asyncio.wait_for(conn.fetch(sql), timeout=timeout)
        else:
            rows = await asyncio.wait_for(conn.fetch(sql), timeout=timeout)
        execution_ms = int((time.monotonic() - start) * 1000)
        columns = list(rows[0].keys()) if rows else []
        return {"columns": columns, "rows": [list(r) for r in rows], "execution_ms": execution_ms}
    finally:
        await conn.close()


async def _execute_sqlite(database: str, sql: str, timeout: float) -> dict:
    async with aiosqlite.connect(database) as conn:
        conn.row_factory = aiosqlite.Row
        start = time.monotonic()
        cursor = await asyncio.wait_for(conn.execute(sql), timeout=timeout)
        rows = await cursor.fetchall()
        execution_ms = int((time.monotonic() - start) * 1000)
        columns = list(rows[0].keys()) if rows else []
        return {"columns": columns, "rows": [list(r) for r in rows], "execution_ms": execution_ms}


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

    Returns:
        {"columns": list[str], "rows": list[list], "execution_ms": int}
    """
    sql = _enforce_limit(sql)

    if db_type == "sqlite":
        return await _execute_sqlite(database, sql, timeout)
    if db_type == "postgres":
        return await _execute_postgres(host, port, database, username, password, sql, timeout, read_only)
    raise NotImplementedError(
        f"Query execution for '{db_type}' is not supported in this version."
    )
