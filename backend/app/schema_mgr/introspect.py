from __future__ import annotations
import asyncpg
import aiosqlite
from app.models.datasource import DBType


async def introspect_postgres(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
) -> list[dict]:
    """Connect to a PostgreSQL datasource and return its public schema."""
    conn = await asyncpg.connect(
        host=host, port=port, database=database, user=username, password=password,
    )
    try:
        tables = await conn.fetch(
            "SELECT table_name "
            "FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
        result = []
        for table_row in tables:
            cols = await conn.fetch(
                "SELECT column_name, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = $1 "
                "ORDER BY ordinal_position",
                table_row["table_name"],
            )
            result.append({
                "table_name": table_row["table_name"],
                "columns": [
                    {"column_name": c["column_name"], "data_type": c["data_type"]}
                    for c in cols
                ],
            })
        return result
    finally:
        await conn.close()


async def introspect_sqlite(database: str) -> list[dict]:
    """Introspect a SQLite database file and return its schema."""
    async with aiosqlite.connect(database) as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        table_names = [row[0] for row in await cursor.fetchall()]
        result = []
        for table_name in table_names:
            cursor = await conn.execute(f"PRAGMA table_info(\"{table_name}\")")
            cols = await cursor.fetchall()
            result.append({
                "table_name": table_name,
                "columns": [
                    {"column_name": col[1], "data_type": col[2] or "TEXT"}
                    for col in cols
                ],
            })
        return result


def check_db_type_supported(db_type: DBType) -> None:
    """Raise ValueError for unsupported datasource types."""
    if db_type not in (DBType.postgres, DBType.sqlite):
        raise ValueError(
            f"Schema sync is not supported for '{db_type.value}' in this version."
        )
