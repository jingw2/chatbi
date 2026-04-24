from app.core.encryption import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    original = "super_secret_password"
    encrypted = encrypt(original)
    assert encrypted != original
    assert decrypt(encrypted) == original


def test_encrypt_produces_different_ciphertext_each_time():
    # Fernet uses random IV, so same plaintext → different ciphertext
    e1 = encrypt("same")
    e2 = encrypt("same")
    assert e1 != e2


def test_decrypt_wrong_key_raises():
    import pytest
    from cryptography.fernet import InvalidToken
    encrypted = encrypt("value")
    # Tamper with ciphertext
    with pytest.raises(Exception):
        decrypt(encrypted[:-4] + "XXXX")
