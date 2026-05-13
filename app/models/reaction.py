import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReactionType(str, enum.Enum):
    like = "like"
    dislike = "dislike"
    love = "love"
    laugh = "laugh"


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_user_post_reaction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    reaction_type: Mapped[ReactionType] = mapped_column(
        Enum(
            ReactionType,
            name="reaction_type",
            values_callable=lambda reaction_types: [item.value for item in reaction_types],
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="reactions")
    post: Mapped["Post"] = relationship(back_populates="reactions")
