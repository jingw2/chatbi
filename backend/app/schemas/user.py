from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: int
    # str (not EmailStr) so internal .local / non-standard domains round-trip cleanly
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    # EmailStr validates proper format at creation time
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
