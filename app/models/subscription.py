from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("subscriber_id", "target_user_id", name="uq_subscriber_target"),
        CheckConstraint("subscriber_id <> target_user_id", name="ck_subscription_not_self"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    target_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    subscriber: Mapped["User"] = relationship(
        foreign_keys=[subscriber_id],
        back_populates="following",
    )
    target_user: Mapped["User"] = relationship(
        foreign_keys=[target_user_id],
        back_populates="followers",
    )
