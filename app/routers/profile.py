from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, get_opt_user
from app.models import Post, Subscription, User
from app.schemas.user import UserUpdate
from app.services.post_cards import build_post_cards


router = APIRouter(tags=["profile"])
templates = Jinja2Templates(directory="app/templates")


def get_form_errors(error: ValidationError) -> dict[str, str]:
    errors = {}
    for item in error.errors():
        field = str(item["loc"][0]) if item["loc"] else "form"
        message = item["msg"].removeprefix("Value error, ")
        errors[field] = message
    return errors


@router.get("/profile")
async def profile_page(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return RedirectResponse(
        f"/users/{current_user.username}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/profile/edit")
async def edit_profile_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return templates.TemplateResponse(
        "edit_profile.html",
        {
            "request": request,
            "user": current_user,
            "errors": {},
            "form_data": {},
            "title": "Редактирование профиля",
        },
    )


@router.post("/profile/edit")
async def edit_profile(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    bio: Annotated[str | None, Form()] = None,
    avatar_url: Annotated[str | None, Form()] = None,
    is_followers_public: Annotated[bool, Form()] = False,
    is_following_public: Annotated[bool, Form()] = False,
):
    form_data = {
        "username": username,
        "email": email,
        "first_name": first_name or "",
        "last_name": last_name or "",
        "bio": bio or "",
        "avatar_url": avatar_url or "",
        "is_followers_public": is_followers_public,
        "is_following_public": is_following_public,
    }

    try:
        user_data = UserUpdate(
            username=username,
            email=email,
            first_name=first_name or None,
            last_name=last_name or None,
            bio=bio or None,
            avatar_url=avatar_url or None,
            is_followers_public=is_followers_public,
            is_following_public=is_following_public,
        )
    except ValidationError as error:
        return templates.TemplateResponse(
            "edit_profile.html",
            {
                "request": request,
                "user": current_user,
                "errors": get_form_errors(error),
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    result = await db.execute(
        select(User).where(
            User.id != current_user.id,
            or_(User.username == user_data.username, User.email == user_data.email),
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        errors = {"username": "Username уже занят"}
        if existing_user.email == str(user_data.email):
            errors = {"email": "Email уже зарегистрирован"}

        return templates.TemplateResponse(
            "edit_profile.html",
            {
                "request": request,
                "user": current_user,
                "errors": errors,
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_user.username = user_data.username
    current_user.email = str(user_data.email)
    current_user.first_name = user_data.first_name
    current_user.last_name = user_data.last_name
    current_user.bio = user_data.bio
    current_user.avatar_url = user_data.avatar_url
    current_user.is_followers_public = user_data.is_followers_public
    current_user.is_following_public = user_data.is_following_public

    await db.commit()

    return RedirectResponse(
        f"/users/{current_user.username}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/users/{username}")
async def user_profile_page(
    username: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_opt_user)],
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    posts_result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.author_id == user.id)
        .order_by(desc(Post.created_at))
    )
    posts = posts_result.scalars().all()
    followers_count = await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.target_user_id == user.id)
    )
    following_count = await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.subscriber_id == user.id)
    )

    is_own_profile = current_user is not None and current_user.id == user.id
    is_subscribed = False
    if current_user is not None and not is_own_profile:
        subscription_result = await db.execute(
            select(Subscription).where(
                Subscription.subscriber_id == current_user.id,
                Subscription.target_user_id == user.id,
            )
        )
        is_subscribed = subscription_result.scalar_one_or_none() is not None

    post_cards = await build_post_cards(db, posts, current_user)

    return templates.TemplateResponse(
        "user_profile.html",
        {
            "request": request,
            "user": user,
            "post_cards": post_cards,
            "current_user": current_user,
            "is_own_profile": is_own_profile,
            "is_subscribed": is_subscribed,
            "followers_count": followers_count,
            "following_count": following_count,
            "title": "Мой профиль" if is_own_profile else f"Профиль {user.username}",
            "show_profile_back": True,
        },
    )


async def get_profile_user_or_404(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    return user


@router.get("/users/{username}/followers")
async def followers_page(
    username: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await get_profile_user_or_404(db, username)
    is_own_profile = current_user.id == user.id

    if not user.is_followers_public and not is_own_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Список подписчиков скрыт",
        )

    result = await db.execute(
        select(User)
        .join(Subscription, Subscription.subscriber_id == User.id)
        .where(Subscription.target_user_id == user.id)
        .order_by(User.username)
    )
    users = result.scalars().all()

    return templates.TemplateResponse(
        "user_list.html",
        {
            "request": request,
            "profile_user": user,
            "users": users,
            "current_user": current_user,
            "list_title": "Подписчики",
            "title": f"Подписчики {user.username}",
        },
    )


@router.get("/users/{username}/following")
async def following_page(
    username: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    user = await get_profile_user_or_404(db, username)
    is_own_profile = current_user.id == user.id

    if not user.is_following_public and not is_own_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Список подписок скрыт",
        )

    result = await db.execute(
        select(User)
        .join(Subscription, Subscription.target_user_id == User.id)
        .where(Subscription.subscriber_id == user.id)
        .order_by(User.username)
    )
    users = result.scalars().all()

    return templates.TemplateResponse(
        "user_list.html",
        {
            "request": request,
            "profile_user": user,
            "users": users,
            "current_user": current_user,
            "list_title": "Подписки",
            "title": f"Подписки {user.username}",
        },
    )
