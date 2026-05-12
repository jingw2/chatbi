from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.encryption import encrypt
from app.llm_gateway import llm_gateway
from app.llm_gateway.base import build_provider
from app.models.model_setting import ModelProvider, ModelRole, ModelSetting
from app.models.user import User, UserRole
from app.schemas.model_setting import (
    ModelSettingResponse,
    ModelSettingTestRequest,
    ModelSettingTestResponse,
    ModelSettingUpdate,
)

router = APIRouter(prefix="/model-settings", tags=["model-settings"])
_admin_roles = (UserRole.superadmin, UserRole.admin)


def _env_defaults(role: ModelRole) -> tuple[ModelProvider, str, str | None, str | None]:
    if role == ModelRole.intent:
        return (
            ModelProvider(settings.intent_model_provider),
            settings.intent_model_name,
            settings.intent_model_base_url or None,
            settings.intent_model_api_key,
        )
    if role == ModelRole.text_to_sql:
        return (
            ModelProvider(settings.text_to_sql_provider),
            settings.text_to_sql_model_name,
            settings.text_to_sql_base_url or None,
            settings.text_to_sql_api_key,
        )
    return (
        ModelProvider(settings.base_model_provider),
        settings.base_model_name,
        settings.base_model_base_url or None,
        settings.base_model_api_key,
    )


def _response_for(role: ModelRole, setting: ModelSetting | None) -> ModelSettingResponse:
    if setting is None:
        provider, model_name, base_url, api_key = _env_defaults(role)
        return ModelSettingResponse(
            role=role,
            provider=provider,
            model_name=model_name,
            base_url=base_url,
            has_api_key=bool(api_key),
            source="env",
        )
    return ModelSettingResponse(
        role=role,
        provider=setting.provider,
        model_name=setting.model_name,
        base_url=setting.base_url,
        has_api_key=bool(setting.encrypted_api_key),
        source="database",
        updated_at=setting.updated_at,
    )


async def _get_settings_map(db: AsyncSession) -> dict[ModelRole, ModelSetting]:
    result = await db.execute(select(ModelSetting))
    return {item.role: item for item in result.scalars().all()}


@router.get("", response_model=list[ModelSettingResponse])
async def list_model_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    current = await _get_settings_map(db)
    return [_response_for(role, current.get(role)) for role in ModelRole]


@router.put("/{role}", response_model=ModelSettingResponse)
async def upsert_model_setting(
    role: ModelRole,
    body: ModelSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_admin_roles)),
):
    setting = await db.get(ModelSetting, role)
    encrypted_api_key = encrypt(body.api_key) if body.api_key is not None else None

    if setting is None:
        setting = ModelSetting(
            role=role,
            provider=body.provider,
            model_name=body.model_name,
            base_url=body.base_url or None,
            encrypted_api_key=encrypted_api_key,
            updated_by=current_user.id,
        )
        db.add(setting)
    else:
        setting.provider = body.provider
        setting.model_name = body.model_name
        setting.base_url = body.base_url or None
        if body.api_key is not None:
            setting.encrypted_api_key = encrypted_api_key
        setting.updated_by = current_user.id

    await db.commit()
    await db.refresh(setting)
    await llm_gateway.reload_from_db(db)
    return _response_for(role, setting)


@router.post("/test", response_model=ModelSettingTestResponse)
async def test_model_setting(
    body: ModelSettingTestRequest,
    _: User = Depends(require_role(*_admin_roles)),
):
    try:
        provider = build_provider(
            body.provider.value,
            body.model_name,
            body.api_key or "none",
            body.base_url or "",
        )
        result = await provider.complete(
            [{"role": "user", "content": "Reply with exactly: ok"}],
            max_tokens=16,
            temperature=0.0,
        )
        return ModelSettingTestResponse(ok=True, message=(result or "").strip() or "ok")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
