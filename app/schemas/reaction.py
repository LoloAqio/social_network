from datetime import datetime

from pydantic import BaseModel

from app.models.reaction import ReactionType


class ReactionCreate(BaseModel):
    reaction_type: ReactionType


class ReactionRead(ReactionCreate):
    id: int
    user_id: int
    post_id: int
    created_at: datetime
