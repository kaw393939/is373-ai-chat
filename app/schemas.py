from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ResetPassword(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=12, max_length=128)


class EmailAddress(BaseModel):
    email: EmailStr


class VerifyEmail(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=12, max_length=128)


class Title(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class Prompt(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    request_key: str = Field(min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    model: str = "default"


class BudgetEdit(BaseModel):
    daily_requests: int = Field(ge=1, le=10000)
    daily_units: int = Field(ge=100, le=10000000)
    max_concurrent: int = Field(ge=1, le=4)
    max_output: int = Field(ge=64, le=4096)
    model_enabled: bool


class UserEdit(BaseModel):
    role: Literal["user", "admin"]
    active: bool
    approved: bool
    daily_requests: int | None = Field(default=None, ge=1, le=10000)
    daily_units: int | None = Field(default=None, ge=100, le=10000000)
    max_concurrent: int | None = Field(default=None, ge=1, le=4)
