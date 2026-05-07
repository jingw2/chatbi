from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.datasource import Datasource
from app.models.user import User, UserRole
from app.models.user_data_scope import UserDataScope
from app.core.encryption import decrypt
from app.llm_gateway import llm_gateway
from app.schema_mgr.retrieval import retrieve_schema
from app.query_engine.knowledge_retrieval import retrieve_knowledge
from app.query_engine.prompt_builder import build_text_to_sql_prompt
from app.query_engine.sql_validator import validate_sql
from app.query_engine.rls import inject_rls
from app.query_engine.executor import execute_query
from app.query_engine.result_processor import sanitize_for_llm, check_result_anomalies
from app.viz.infer import infer_chart_type
from app.viz.config import build_chart_config

_VALID_INTENTS = {"data_query", "definition", "clarify", "fixed_workflow", "chitchat"}

_INTENT_SYSTEM = (
    "Classify the user's question into exactly one category: "
    "data_query, definition, clarify, chitchat. "
    "Respond with ONLY the category name."
)

_INSIGHT_SYSTEM = (
    "Based on the query results, provide:\n"
    "1. A concise insight (2-3 sentences) about key findings\n"
    "2. 2-3 actionable business suggestions\n\n"
    "Format exactly as:\n"
    "INSIGHT: <text>\n"
    "SUGGESTION: <text>\n"
    "SUGGESTION: <text>\n"
    "SUGGESTION: <text (optional)>"
)


@dataclass
class PipelineResult:
    intent: str
    sql: str | None
    columns: list[str]
    rows: list[list]
    chart_type: str | None
    chart_config: dict | None
    insight: str | None
    suggestions: list[str]
    error: str | None
    execution_ms: int | None
    warnings: list[str] = field(default_factory=list)


async def run_pipeline(
    question: str,
    datasource_id: int,
    user: User,
    db: AsyncSession,
    max_sql_retries: int = 3,
) -> PipelineResult:
    """Execute the full 9-step query pipeline.

    Steps:
    1. Intent recognition
    2. Schema retrieval (Qdrant + bge-reranker)
    3. Knowledge retrieval (Qdrant + bge-reranker)
    4. Prompt construction
    5. SQL generation + validation (with retries)
    6. RLS injection
    7. Query execution (asyncpg)
    8. Result processing (anomaly check + chart inference)
    9. Insight + decision suggestions (LLM)
    """
    # Step 1: Intent
    intent_raw = await llm_gateway.intent(question, system=_INTENT_SYSTEM)
    intent = intent_raw.strip().lower()
    if intent not in _VALID_INTENTS:
        intent = "data_query"

    if intent != "data_query":
        return PipelineResult(
            intent=intent, sql=None, columns=[], rows=[],
            chart_type=None, chart_config=None, insight=None, suggestions=[], error=None, execution_ms=None,
        )

    # Fetch datasource
    ds_row = await db.execute(select(Datasource).where(Datasource.id == datasource_id))
    ds = ds_row.scalar_one_or_none()
    if ds is None:
        return PipelineResult(
            intent=intent, sql=None, columns=[], rows=[],
            chart_type=None, chart_config=None, insight=None, suggestions=[],
            error="Datasource not found", execution_ms=None,
        )

    # Step 2+3: Retrieval
    schema_cols = await retrieve_schema(question, datasource_id, db, top_k=5)
    knowledge_items = await retrieve_knowledge(question, datasource_id, db, top_k=5)

    # Step 4: Prompt construction
    prompt = build_text_to_sql_prompt(question, schema_cols, knowledge_items)

    # Fetch allowed table names for SQL validation
    from app.models.schema_table import SchemaTable  # local import to avoid circular
    tbl_rows = await db.execute(
        select(SchemaTable.table_name).where(
            SchemaTable.datasource_id == datasource_id,
            SchemaTable.is_active.is_(True),
        )
    )
    allowed_tables = {row[0] for row in tbl_rows.all()}

    # Step 5: SQL generation + validation (retry loop)
    sql: str | None = None
    last_error = ""
    retry_prompt = prompt
    for attempt in range(max_sql_retries):
        raw = await llm_gateway.text_to_sql(retry_prompt)
        candidate = _extract_sql(raw)
        ok, err = validate_sql(candidate, allowed_tables)
        if ok:
            sql = candidate
            last_error = ""
            break
        last_error = f"SQL validation failed: {err}"
        retry_prompt = retry_prompt + f"\n\n上次生成的SQL无效: {err}\n请重新生成有效的SQL查询。"

    if sql is None:
        return PipelineResult(
            intent=intent, sql=None, columns=[], rows=[],
            chart_type=None, chart_config=None, insight=None, suggestions=[],
            error=last_error, execution_ms=None,
        )

    # Step 6: RLS injection
    scopes = await _get_user_scopes(user.id, db)
    sql = inject_rls(sql, scopes, user.role.value)

    # Step 7: Query execution
    password = decrypt(ds.readonly_encrypted_password)
    try:
        exec_result = await execute_query(
            host=ds.host, port=ds.port, database=ds.database,
            username=ds.readonly_user, password=password, sql=sql,
        )
    except Exception as exc:
        return PipelineResult(
            intent=intent, sql=sql, columns=[], rows=[],
            chart_type=None, chart_config=None, insight=None, suggestions=[],
            error=str(exc), execution_ms=None,
        )

    columns = exec_result["columns"]
    rows = exec_result["rows"]
    execution_ms = exec_result["execution_ms"]

    # Step 8: Result processing
    warnings = check_result_anomalies(columns, rows)
    chart_type = infer_chart_type(columns, rows) if rows else None
    chart_config = build_chart_config(chart_type, columns, rows) if chart_type else None
    data_str = sanitize_for_llm(columns, rows)

    # Step 9: Insight + suggestions
    insight, suggestions = await _generate_insight(question, data_str, warnings)

    return PipelineResult(
        intent=intent, sql=sql, columns=columns, rows=rows,
        chart_type=chart_type, chart_config=chart_config, insight=insight, suggestions=suggestions,
        error=None, execution_ms=execution_ms, warnings=warnings,
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_sql(text: str) -> str:
    """Strip markdown fences and extra whitespace from LLM SQL response."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.lower().startswith("sql"):
                cleaned = cleaned[3:].strip()
            if cleaned.upper().lstrip().startswith("SELECT"):
                return cleaned
    return text


async def _get_user_scopes(user_id: int, db: AsyncSession) -> dict[str, str]:
    result = await db.execute(
        select(UserDataScope).where(UserDataScope.user_id == user_id)
    )
    return {s.scope_key: s.scope_value for s in result.scalars().all()}


async def _generate_insight(
    question: str, data_str: str, warnings: list[str]
) -> tuple[str, list[str]]:
    user_prompt = f"Question: {question}\n\nData:\n{data_str}"
    if warnings:
        user_prompt += f"\n\nWarnings: {'; '.join(warnings)}"

    response = await llm_gateway.base(user_prompt, system=_INSIGHT_SYSTEM)

    insight = ""
    suggestions: list[str] = []
    for line in response.strip().split("\n"):
        if line.startswith("INSIGHT:"):
            insight = line[8:].strip()
        elif line.startswith("SUGGESTION:"):
            suggestions.append(line[11:].strip())

    return insight or response.strip(), suggestions[:3]
