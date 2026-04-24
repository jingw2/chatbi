import pytest
from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_refresh_token,
)


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False
    assert hashed != "mysecret"  # must not store plaintext


def test_hash_is_different_each_time():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salts differ


def test_access_token_roundtrip():
    token = create_access_token({"sub": "42", "role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_expired_token_raises():
    token = create_access_token(
        {"sub": "42"}, expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(Exception):
        decode_access_token(token)


def test_refresh_token_has_type_field():
    token = create_refresh_token(99)
    payload = decode_access_token(token)
    assert payload["sub"] == "99"
    assert payload["type"] == "refresh"
