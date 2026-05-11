import pytest
from httpx import AsyncClient

from app.core.encryption import decrypt
from app.core.security import create_access_token, hash_password
from app.models.model_setting import ModelRole, ModelSetting
from app.models.user import User, UserRole


def auth_header(user_id: int, role: str = "admin") -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


async def _admin(db_session):
    user = User(
        email="model-admin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_list_model_settings_returns_three_roles(client: AsyncClient, db_session):
    admin = await _admin(db_session)

    response = await client.get(
        "/api/v1/model-settings",
        headers=auth_header(admin.id),
    )

    assert response.status_code == 200
    roles = {item["role"] for item in response.json()}
    assert roles == {"intent", "text_to_sql", "base"}
    assert all("api_key" not in item for item in response.json())


@pytest.mark.asyncio
async def test_upsert_model_setting_encrypts_key_and_does_not_echo_it(
    client: AsyncClient, db_session
):
    admin = await _admin(db_session)

    response = await client.put(
        "/api/v1/model-settings/text_to_sql",
        json={
            "provider": "openai_compatible",
            "base_url": "http://127.0.0.1:8001/v1",
            "model_name": "chatbi-sql",
            "api_key": "none",
        },
        headers=auth_header(admin.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "text_to_sql"
    assert data["has_api_key"] is True
    assert "api_key" not in data

    setting = await db_session.get(ModelSetting, ModelRole.text_to_sql)
    assert setting is not None
    assert decrypt(setting.encrypted_api_key) == "none"


@pytest.mark.asyncio
async def test_model_settings_require_admin(client: AsyncClient, db_session):
    viewer = User(
        email="model-viewer@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.viewer,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)

    response = await client.get(
        "/api/v1/model-settings",
        headers=auth_header(viewer.id, "viewer"),
    )

    assert response.status_code == 403
