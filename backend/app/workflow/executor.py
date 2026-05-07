from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.encryption import decrypt
from app.query_engine.executor import execute_query


@dataclass
class WorkflowResult:
    workflow_name: str
    step_results: list[dict]
    total_execution_ms: int
    error: str | None


async def run_workflow(workflow, datasource) -> WorkflowResult:
    """Execute all steps in a workflow definition sequentially.

    Each step has {"name": str, "sql": str}. Steps are executed in order
    against the datasource's read-only connection. If a step fails, its
    error is recorded but execution continues with the next step.

    Returns a WorkflowResult with per-step columns/rows/error.
    """
    password = decrypt(datasource.readonly_encrypted_password)
    step_results: list[dict] = []
    total_ms = 0

    for step in (workflow.steps or []):
        step_name = step.get("name", "unnamed")
        step_sql = step.get("sql", "")

        try:
            exec_result = await execute_query(
                host=datasource.host,
                port=datasource.port,
                database=datasource.database,
                username=datasource.readonly_user,
                password=password,
                sql=step_sql,
            )
            step_results.append({
                "name": step_name,
                "columns": exec_result["columns"],
                "rows": exec_result["rows"],
                "execution_ms": exec_result["execution_ms"],
                "error": None,
            })
            total_ms += exec_result["execution_ms"]
        except Exception as exc:
            step_results.append({
                "name": step_name,
                "columns": [],
                "rows": [],
                "execution_ms": 0,
                "error": str(exc),
            })

    return WorkflowResult(
        workflow_name=workflow.name,
        step_results=step_results,
        total_execution_ms=total_ms,
        error=None,
    )
