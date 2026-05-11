from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.model_setting import ModelProvider, ModelRole


class ModelSettingResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    role: ModelRole
    provider: ModelProvider
    model_name: str
    base_url: str | None
    has_api_key: bool
    source: str
    updated_at: datetime | None = None


class ModelSettingUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: ModelProvider
    model_name: str
    base_url: str | None = None
    api_key: str | None = None


class ModelSettingTestRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: ModelProvider
    model_name: str
    base_url: str | None = None
    api_key: str | None = None


class ModelSettingTestResponse(BaseModel):
    ok: bool
    message: str
