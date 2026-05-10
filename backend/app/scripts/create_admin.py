"""Create the first admin user.

Usage:
    python -m app.scripts.create_admin [--email EMAIL] [--password PASSWORD]

If flags are omitted, prompts interactively (or uses defaults in non-interactive mode).
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine
from app.models.user import User, UserRole
from app.core.security import hash_password


async def _create_admin(email: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"User '{email}' already exists — skipping.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.superadmin,
        )
        db.add(user)
        await db.commit()
        print(f"Admin user created: {email} (role=superadmin)")


def main():
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--email", default="admin@chatbi.local")
    parser.add_argument("--password", default="admin123")
    args = parser.parse_args()

    asyncio.run(_create_admin(args.email, args.password))


if __name__ == "__main__":
    main()
