import pytest
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token, create_refresh_token


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session):
    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.analyst,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session):
    user = User(
        email="test2@example.com",
        hashed_password=hash_password("correct"),
        role=UserRole.viewer,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test2@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, db_session):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "pass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, db_session):
    user = User(
        email="me@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_header(user.id, "admin"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_api(client: AsyncClient, db_session):
    user = User(
        email="refresh@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.viewer,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {create_refresh_token(user.id)}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_allows_local_admin_email(client: AsyncClient, db_session):
    user = User(
        email="admin@chatbi.local",
        hashed_password=hash_password("admin123"),
        role=UserRole.superadmin,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@chatbi.local", "password": "admin123"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
