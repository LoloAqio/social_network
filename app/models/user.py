from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_followers_public: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_following_public: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[list["Reaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    following: Mapped[list["Subscription"]] = relationship(
        foreign_keys="Subscription.subscriber_id",
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )
    followers: Mapped[list["Subscription"]] = relationship(
        foreign_keys="Subscription.target_user_id",
        back_populates="target_user",
        cascade="all, delete-orphan",
    )
