import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.constants import DEPARTMENTS

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Enter a valid email address.")
    return email


def _clean_name(value: str) -> str:
    name = " ".join(value.split())
    if not name:
        raise ValueError("Name cannot be empty.")
    return name


def _check_department(value: str) -> str:
    if value not in DEPARTMENTS:
        raise ValueError(f"Department must be one of: {', '.join(DEPARTMENTS)}.")
    return value


class RegisterRequest(BaseModel):
    """Faculty self-registration. The role cannot be chosen here; it is always 'faculty'."""

    name: str = Field(..., max_length=100)
    email: str
    password: str = Field(..., min_length=6, max_length=128)
    department: str
    designation: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)

    _name = field_validator("name")(_clean_name)
    _email = field_validator("email")(_clean_email)
    _department = field_validator("department")(_check_department)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=1)

    _email = field_validator("email")(_clean_email)


class UpdateProfileRequest(BaseModel):
    """Editable profile fields. Email and role cannot be changed."""

    name: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = None
    designation: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)

    @field_validator("name")
    @classmethod
    def _name(cls, value):
        return None if value is None else _clean_name(value)

    @field_validator("department")
    @classmethod
    def _department(cls, value):
        return None if value is None else _check_department(value)


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic
