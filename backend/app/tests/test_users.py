import pytest
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_user_as_superadmin(client: AsyncClient, db_session):
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.superadmin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.post(
        "/api/v1/users",
        json={"email": "new@example.com", "password": "pass123", "role": "viewer"},
        headers=auth_header(admin.id, "superadmin"),
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"
    assert response.json()["role"] == "viewer"


@pytest.mark.asyncio
async def test_create_user_as_viewer_forbidden(client: AsyncClient, db_session):
    viewer = User(
        email="viewer@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.viewer,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)

    response = await client.post(
        "/api/v1/users",
        json={"email": "other@example.com", "password": "pass", "role": "viewer"},
        headers=auth_header(viewer.id, "viewer"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_duplicate_user_returns_409(client: AsyncClient, db_session):
    admin = User(
        email="admin2@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.superadmin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    await client.post(
        "/api/v1/users",
        json={"email": "dup@example.com", "password": "pass", "role": "viewer"},
        headers=auth_header(admin.id, "superadmin"),
    )
    response = await client.post(
        "/api/v1/users",
        json={"email": "dup@example.com", "password": "pass", "role": "viewer"},
        headers=auth_header(admin.id, "superadmin"),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_users_as_admin(client: AsyncClient, db_session):
    admin = User(
        email="admin3@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.get(
        "/api/v1/users",
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_user_role(client: AsyncClient, db_session):
    admin = User(
        email="admin4@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.superadmin,
    )
    target = User(
        email="target@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.viewer,
    )
    db_session.add_all([admin, target])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(target)

    response = await client.patch(
        f"/api/v1/users/{target.id}",
        json={"role": "analyst"},
        headers=auth_header(admin.id, "superadmin"),
    )
    assert response.status_code == 200
    assert response.json()["role"] == "analyst"
