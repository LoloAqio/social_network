from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, get_opt_user
from app.models import Post, Subscription, User
from app.services.post_cards import build_post_cards


router = APIRouter(tags=["feed"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/feed")
async def feed_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_opt_user)],
):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))
        .order_by(desc(Post.created_at))
    )
    posts = result.scalars().all()
    post_cards = await build_post_cards(db, posts, current_user)

    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "post_cards": post_cards,
            "current_user": current_user,
            "title": "Лента",
            "heading": "Лента",
            "empty_message": "Постов пока нет.",
        },
    )


@router.get("/following-feed")
async def following_feed_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Post)
        .join(Subscription, Subscription.target_user_id == Post.author_id)
        .options(selectinload(Post.author))
        .where(Subscription.subscriber_id == current_user.id)
        .order_by(desc(Post.created_at))
    )
    posts = result.scalars().all()
    post_cards = await build_post_cards(db, posts, current_user)

    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "post_cards": post_cards,
            "current_user": current_user,
            "title": "Лента подписок",
            "heading": "Лента подписок",
            "empty_message": "У пользователей, на которых вы подписаны, пока нет постов.",
        },
    )
