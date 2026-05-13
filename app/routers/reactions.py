from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Post, Reaction, User
from app.schemas.reaction import ReactionCreate
from app.services.reactions import get_reaction_counts_for_post


router = APIRouter(tags=["reactions"])


def get_safe_next(next_url: str | None) -> str | None:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return None


async def get_post_or_404(db: AsyncSession, post_id: int) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    return post


@router.post("/posts/{post_id}/reactions")
async def react_to_post(
    post_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    reaction_type: Annotated[str, Form()],
    next: Annotated[str | None, Form()] = None,
):
    post = await get_post_or_404(db, post_id)
    wants_json = request.headers.get("x-requested-with") == "XMLHttpRequest"

    try:
        reaction_data = ReactionCreate(reaction_type=reaction_type)
    except ValidationError:
        if wants_json:
            return JSONResponse(
                {"detail": "Invalid reaction type"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reaction type",
        )

    result = await db.execute(
        select(Reaction).where(
            Reaction.user_id == current_user.id,
            Reaction.post_id == post.id,
        )
    )
    reaction = result.scalar_one_or_none()
    current_user_reaction = reaction_data.reaction_type.value

    if reaction is None:
        db.add(
            Reaction(
                user_id=current_user.id,
                post_id=post.id,
                reaction_type=reaction_data.reaction_type,
            )
        )
    elif reaction.reaction_type == reaction_data.reaction_type:
        await db.delete(reaction)
        current_user_reaction = None
    else:
        reaction.reaction_type = reaction_data.reaction_type

    await db.commit()

    if wants_json:
        return JSONResponse(
            {
                "post_id": post.id,
                "current_user_reaction": current_user_reaction,
                "reaction_counts": await get_reaction_counts_for_post(db, post.id),
            }
        )

    return RedirectResponse(
        get_safe_next(next) or f"/posts/{post.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
