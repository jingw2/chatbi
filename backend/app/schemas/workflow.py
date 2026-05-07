from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class WorkflowStepDef(BaseModel):
    name: str
    sql: str


class WorkflowCreate(BaseModel):
    name: str
    datasource_id: int
    trigger_keywords: list[str]
    steps: list[WorkflowStepDef]


class WorkflowUpdate(BaseModel):
    name: str | None = None
    trigger_keywords: list[str] | None = None
    steps: list[WorkflowStepDef] | None = None
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    id: int
    name: str
    datasource_id: int
    trigger_keywords: list[str]
    steps: list[dict]
    created_by: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
