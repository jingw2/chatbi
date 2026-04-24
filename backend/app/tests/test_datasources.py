import pytest
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_datasource_as_admin(client: AsyncClient, db_session):
    admin = User(
        email="dsadmin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.post(
        "/api/v1/datasources",
        json={
            "name": "Prod DB",
            "db_type": "postgres",
            "host": "db.example.com",
            "port": 5432,
            "database": "production",
            "username": "app_user",
            "password": "secret",
            "readonly_user": "readonly",
            "readonly_password": "readonly_secret",
        },
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Prod DB"
    assert data["db_type"] == "postgres"
    assert "password" not in data
    assert "encrypted_password" not in data


@pytest.mark.asyncio
async def test_create_datasource_as_viewer_forbidden(client: AsyncClient, db_session):
    viewer = User(
        email="viewer@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.viewer,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)

    response = await client.post(
        "/api/v1/datasources",
        json={
            "name": "X",
            "db_type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database": "db",
            "username": "u",
            "password": "p",
            "readonly_user": "r",
            "readonly_password": "rp",
        },
        headers=auth_header(viewer.id, "viewer"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_datasources_as_admin(client: AsyncClient, db_session):
    admin = User(
        email="dsadmin2@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.get(
        "/api/v1/datasources",
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_datasource_requires_superadmin(client: AsyncClient, db_session):
    admin = User(
        email="dsadmin3@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.delete(
        "/api/v1/datasources/999",
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_datasource_not_found(client: AsyncClient, db_session):
    superadmin = User(
        email="sa_delete@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.superadmin,
    )
    db_session.add(superadmin)
    await db_session.commit()
    await db_session.refresh(superadmin)

    response = await client.delete(
        "/api/v1/datasources/999999",
        headers=auth_header(superadmin.id, "superadmin"),
    )
    assert response.status_code == 404
