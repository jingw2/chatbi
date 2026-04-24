from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.encryption import encrypt
from app.models.datasource import Datasource
from app.models.user import User, UserRole
from app.schemas.datasource import DatasourceCreate, DatasourceResponse
from app.api.deps import require_role

router = APIRouter(prefix="/datasources", tags=["datasources"])

_admin_roles = (UserRole.superadmin, UserRole.admin)


@router.get("", response_model=list[DatasourceResponse])
async def list_datasources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(select(Datasource))
    return result.scalars().all()


@router.post("", response_model=DatasourceResponse, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    body: DatasourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_admin_roles)),
):
    ds = Datasource(
        name=body.name,
        db_type=body.db_type,
        host=body.host,
        port=body.port,
        database=body.database,
        username=body.username,
        encrypted_password=encrypt(body.password),
        readonly_user=body.readonly_user,
        readonly_encrypted_password=encrypt(body.readonly_password),
        created_by=current_user.id,
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return ds


@router.delete("/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.superadmin)),
):
    result = await db.execute(select(Datasource).where(Datasource.id == datasource_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")
    await db.delete(ds)
    await db.commit()
