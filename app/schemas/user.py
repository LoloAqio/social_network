from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=255)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Username должен содержать минимум 3 символа")
        if " " in value:
            raise ValueError("Username не должен содержать пробелы")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Введите email в формате name@example.com")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if not value:
            return None
        if " " in value:
            raise ValueError("Поле не должно содержать пробелы")
        return value


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        return value


class UserRead(UserBase):
    id: int
    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    is_followers_public: bool
    is_following_public: bool
    created_at: datetime


class UserUpdate(BaseModel):
    username: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    is_followers_public: bool = True
    is_following_public: bool = True

    @field_validator("username")
    @classmethod
    def validate_update_username(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if len(value) < 3:
            raise ValueError("Username должен содержать минимум 3 символа")
        if " " in value:
            raise ValueError("Username не должен содержать пробелы")
        return value

    @field_validator("email")
    @classmethod
    def validate_update_email(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Введите email в формате name@example.com")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_update_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if not value:
            return None
        if " " in value:
            raise ValueError("Поле не должно содержать пробелы")
        return value


class UserLogin(BaseModel):
    login: str = Field(..., min_length=3, max_length=255)
    password: str
