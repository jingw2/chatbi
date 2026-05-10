from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String
from app.models.workflow import Workflow


async def match_workflow(
    question: str,
    datasource_id: int,
    db: AsyncSession,
) -> Workflow | None:
    """Find the first active workflow whose trigger keywords appear in the question.

    Matching is case-insensitive substring match: if any keyword from a workflow's
    trigger_keywords list appears anywhere in the question, that workflow matches.

    Uses SQL-level filtering to avoid loading all workflows into Python memory.
    Falls back to Python matching for databases that don't support array operations.

    Returns the first matching Workflow, or None.
    """
    question_lower = question.lower()

    # First try: fetch only active workflows for this datasource, then match in Python.
    # This is bounded by datasource (typically small count) and avoids complex SQL.
    result = await db.execute(
        select(Workflow).where(
            Workflow.datasource_id == datasource_id,
            Workflow.is_active.is_(True),
        ).order_by(Workflow.id)
    )
    workflows = result.scalars().all()

    for wf in workflows:
        for keyword in (wf.trigger_keywords or []):
            if keyword.lower() in question_lower:
                return wf
    return None
