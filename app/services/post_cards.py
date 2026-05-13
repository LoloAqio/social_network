from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, Reaction, ReactionType, User
from app.services.reactions import get_reaction_counts_by_post_ids


@dataclass(frozen=True)
class PostCard:
    post: Post
    reaction_counts: dict[str, int]
    current_user_reaction: ReactionType | None
    can_react: bool
    can_edit: bool
    can_delete: bool


async def build_post_cards(
    db: AsyncSession,
    posts: list[Post],
    current_user: User | None = None,
) -> list[PostCard]:
    post_ids = [post.id for post in posts]
    reaction_counts = await get_reaction_counts_by_post_ids(db, post_ids)
    user_reactions: dict[int, ReactionType] = {}

    if current_user is not None and post_ids:
        result = await db.execute(
            select(Reaction).where(
                Reaction.user_id == current_user.id,
                Reaction.post_id.in_(post_ids),
            )
        )
        user_reactions = {
            reaction.post_id: reaction.reaction_type
            for reaction in result.scalars().all()
        }

    post_cards: list[PostCard] = []
    for post in posts:
        is_author = current_user is not None and post.author_id == current_user.id
        post_cards.append(
            PostCard(
                post=post,
                reaction_counts=reaction_counts[post.id],
                current_user_reaction=user_reactions.get(post.id),
                can_react=current_user is not None,
                can_edit=is_author,
                can_delete=is_author,
            )
        )

    return post_cards
