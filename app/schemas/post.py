from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PostBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=280)

    @field_validator("content")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: str | None = Field(None, min_length=1, max_length=280)

    @field_validator("content")
    @classmethod
    def validate_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class PostRead(PostBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
