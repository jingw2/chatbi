from __future__ import annotations
import asyncpg
from app.models.datasource import DBType


async def introspect_postgres(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
) -> list[dict]:
    """Connect to a PostgreSQL datasource and return its public schema.

    Returns a list of tables, each with a list of columns:
        [{"table_name": str, "columns": [{"column_name": str, "data_type": str}]}]
    """
    conn = await asyncpg.connect(
        host=host,
        port=port,
        database=database,
        user=username,
        password=password,
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
            result.append(
                {
                    "table_name": table_row["table_name"],
                    "columns": [
                        {
                            "column_name": c["column_name"],
                            "data_type": c["data_type"],
                        }
                        for c in cols
                    ],
                }
            )
        return result
    finally:
        await conn.close()


def check_db_type_supported(db_type: DBType) -> None:
    """Raise ValueError for unsupported datasource types."""
    if db_type != DBType.postgres:
        raise ValueError(
            f"Schema sync is only supported for PostgreSQL in this version. "
            f"Got: {db_type.value}"
        )
