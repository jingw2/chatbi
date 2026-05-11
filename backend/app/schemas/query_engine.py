from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    datasource_id: int
    title: str | None = None  # defaults to first 30 chars of first question


class ConversationUpdate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    datasource_id: int | None
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    question: str


class WorkflowStepResult(BaseModel):
    name: str
    columns: list[str]
    rows: list[list]
    execution_ms: int
    error: str | None


class WorkflowResultResponse(BaseModel):
    workflow_name: str
    step_results: list[WorkflowStepResult]
    total_execution_ms: int
    error: str | None


class QueryResponse(BaseModel):
    query_log_id: int
    intent: str
    sql: str | None
    columns: list[str]
    rows: list[list]
    chart_type: str | None
    chart_config: dict | None
    insight: str | None
    suggestions: list[str]
    warnings: list[str]
    error: str | None
    execution_ms: int | None
    workflow_result: WorkflowResultResponse | None = None
