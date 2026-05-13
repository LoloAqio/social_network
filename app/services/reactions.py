from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reaction, ReactionType


def empty_reaction_counts() -> dict[str, int]:
    return {reaction_type.value: 0 for reaction_type in ReactionType}


async def get_reaction_counts_by_post_ids(
    db: AsyncSession,
    post_ids: list[int],
) -> dict[int, dict[str, int]]:
    counts = {post_id: empty_reaction_counts() for post_id in post_ids}
    if not post_ids:
        return counts

    result = await db.execute(
        select(Reaction.post_id, Reaction.reaction_type, func.count())
        .where(Reaction.post_id.in_(post_ids))
        .group_by(Reaction.post_id, Reaction.reaction_type)
    )

    for post_id, reaction_type, count in result.all():
        counts[post_id][reaction_type.value] = count

    return counts


async def get_reaction_counts_for_post(
    db: AsyncSession,
    post_id: int,
) -> dict[str, int]:
    counts = await get_reaction_counts_by_post_ids(db, [post_id])
    return counts[post_id]
