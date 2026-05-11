from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
import app.llm_gateway   # noqa: F401 — triggers singleton creation at startup
import app.embedding     # noqa: F401 — initialises EmbeddingService singleton
import app.qdrant_store  # noqa: F401 — initialises vector store singleton


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-create tables + admin user in lite (SQLite) mode."""
    if settings.is_lite:
        from app.core.database import engine, Base
        import app.models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Ensure at least one admin user exists
        from app.core.database import AsyncSessionLocal
        from app.models.user import User, UserRole
        from app.core.security import hash_password
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.email == "admin@chatbi.local").limit(1)
            )
            if not result.scalar_one_or_none():
                db.add(User(
                    email="admin@chatbi.local",
                    hashed_password=hash_password("admin123"),
                    role=UserRole.superadmin,
                ))
                await db.commit()
                print("Lite mode: created default admin (admin@chatbi.local / admin123)")

        # Ensure vector store collections exist
        from app.qdrant_store import qdrant_store
        await qdrant_store.ensure_collection("schema_columns")
        await qdrant_store.ensure_collection("knowledge_items")

    yield


app = FastAPI(title="ChatBI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "lite" if settings.is_lite else "production"}
