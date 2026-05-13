from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Post, User
from app.schemas.post import PostCreate, PostUpdate


router = APIRouter(prefix="/posts", tags=["posts"])
templates = Jinja2Templates(directory="app/templates")


def get_first_validation_message(error: ValidationError) -> str:
    message = error.errors()[0]["msg"]
    return message.removeprefix("Value error, ")


def get_safe_next(next_url: str | None) -> str | None:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return None


async def get_post_or_404(db: AsyncSession, post_id: int) -> Post:
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден",
        )

    return post


@router.get("/create")
async def create_post_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    next: str | None = None,
):
    safe_next = get_safe_next(next)
    return templates.TemplateResponse(
        "create_post.html",
        {
            "request": request,
            "current_user": current_user,
            "errors": {},
            "content": "",
            "next": safe_next,
            "published": False,
            "redirect_url": safe_next or f"/users/{current_user.username}",
            "title": "Создание поста",
            "show_post_back": True,
            "post_back_href": safe_next or f"/users/{current_user.username}",
        },
    )


@router.post("/create")
async def create_post(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form()],
    next: Annotated[str | None, Form()] = None,
):
    safe_next = get_safe_next(next)
    try:
        post_data = PostCreate(content=content)
    except ValidationError as error:
        return templates.TemplateResponse(
            "create_post.html",
            {
                "request": request,
                "current_user": current_user,
                "errors": {"content": get_first_validation_message(error)},
                "content": content,
                "next": safe_next,
                "published": False,
                "redirect_url": safe_next or f"/users/{current_user.username}",
                "title": "Создание поста",
                "show_post_back": True,
                "post_back_href": safe_next or f"/users/{current_user.username}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    post = Post(
        author_id=current_user.id,
        content=post_data.content,
    )

    db.add(post)
    await db.commit()

    return templates.TemplateResponse(
        "create_post.html",
        {
            "request": request,
            "current_user": current_user,
            "errors": {},
            "content": post_data.content,
            "next": safe_next,
            "published": True,
            "redirect_url": safe_next or f"/users/{current_user.username}",
            "title": "Пост опубликован",
            "show_post_back": True,
            "post_back_href": safe_next or f"/users/{current_user.username}",
        },
    )


@router.get("/{post_id}/edit")
async def edit_post_page(
    post_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    next: str | None = None,
):
    post = await get_post_or_404(db, post_id)

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Можно редактировать только свои посты",
        )

    safe_next = get_safe_next(next)
    return templates.TemplateResponse(
        "edit_post.html",
        {
            "request": request,
            "post": post,
            "current_user": current_user,
            "errors": {},
            "next": safe_next,
            "title": "Редактирование поста",
            "show_post_back": True,
            "post_back_href": safe_next or f"/users/{current_user.username}",
        },
    )


@router.post("/{post_id}/edit")
async def edit_post(
    post_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    content: Annotated[str, Form()],
    next: Annotated[str | None, Form()] = None,
):
    safe_next = get_safe_next(next)
    post = await get_post_or_404(db, post_id)

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Можно редактировать только свои посты",
        )

    try:
        post_data = PostUpdate(content=content)
    except ValidationError as error:
        return templates.TemplateResponse(
            "edit_post.html",
            {
                "request": request,
                "post": post,
                "current_user": current_user,
                "errors": {"content": get_first_validation_message(error)},
                "content": content,
                "next": safe_next,
                "show_post_back": True,
                "post_back_href": safe_next or f"/users/{current_user.username}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    post.content = post_data.content
    await db.commit()

    return RedirectResponse(safe_next or f"/users/{current_user.username}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{post_id}/delete")
async def delete_post(
    post_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    post = await get_post_or_404(db, post_id)

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Можно удалять только свои посты",
        )

    await db.delete(post)
    await db.commit()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JSONResponse({"deleted": True, "post_id": post_id})

    return RedirectResponse(f"/users/{current_user.username}", status_code=status.HTTP_303_SEE_OTHER)
