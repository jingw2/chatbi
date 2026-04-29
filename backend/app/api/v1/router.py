from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.datasources import router as datasources_router
from app.schema_mgr.router import router as schema_router
from app.knowledge.router import router as knowledge_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(datasources_router)
api_router.include_router(schema_router)
api_router.include_router(knowledge_router)
