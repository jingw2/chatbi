"""Initialize database tables from ORM metadata.

For lite mode (SQLite), this creates all tables directly — no Alembic needed.
For production (PostgreSQL), use `alembic upgrade head` instead.

Usage:
    python -m app.scripts.init_db
"""
from __future__ import annotations

import asyncio
from app.core.database import engine, Base
import app.models  # noqa: F401 — registers all models with Base.metadata


async def _init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")


def main():
    asyncio.run(_init_db())


if __name__ == "__main__":
    main()
