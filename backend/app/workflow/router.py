from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.workflow import Workflow
from app.models.user import User, UserRole
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
)
from app.api.deps import require_role

router = APIRouter(prefix="/workflows", tags=["workflows"])
_admin_roles = (UserRole.superadmin, UserRole.admin)


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(
        select(Workflow).where(Workflow.datasource_id == datasource_id)
    )
    return result.scalars().all()


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_admin_roles)),
):
    wf = Workflow(
        name=body.name,
        datasource_id=body.datasource_id,
        trigger_keywords=body.trigger_keywords,
        steps=[s.model_dump() for s in body.steps],
        created_by=current_user.id,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    body: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if body.name is not None:
        wf.name = body.name
    if body.trigger_keywords is not None:
        wf.trigger_keywords = body.trigger_keywords
    if body.steps is not None:
        wf.steps = [s.model_dump() for s in body.steps]
    if body.is_active is not None:
        wf.is_active = body.is_active

    await db.commit()
    await db.refresh(wf)
    return wf


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(wf)
    await db.commit()
