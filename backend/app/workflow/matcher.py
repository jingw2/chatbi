from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.workflow import Workflow


async def match_workflow(
    question: str,
    datasource_id: int,
    db: AsyncSession,
) -> Workflow | None:
    """Find the first active workflow whose trigger keywords appear in the question.

    Matching is case-insensitive substring match: if any keyword from a workflow's
    trigger_keywords list appears anywhere in the question, that workflow matches.

    Returns the first matching Workflow, or None.
    """
    result = await db.execute(
        select(Workflow).where(
            Workflow.datasource_id == datasource_id,
            Workflow.is_active.is_(True),
        )
    )
    workflows = result.scalars().all()

    question_lower = question.lower()
    for wf in workflows:
        for keyword in (wf.trigger_keywords or []):
            if keyword.lower() in question_lower:
                return wf
    return None
