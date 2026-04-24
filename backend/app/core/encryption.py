import base64
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    # Derive a 32-byte Fernet key from the hex encryption_key setting.
    # Pad/truncate to 32 bytes, then base64url-encode as Fernet requires.
    raw = settings.encryption_key.encode()[:32].ljust(32, b"0")
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)


def encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()
