from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    # Use str (not EmailStr) — login looks up by email string, no re-validation needed.
    # EmailStr validation happens at user-creation time (UserCreate schema).
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
