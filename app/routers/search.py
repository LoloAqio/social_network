from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_opt_user
from app.models import User


router = APIRouter(tags=["search"])
templates = Jinja2Templates(directory="app/templates")
SEARCH_LIMIT = 20


@router.get("/search")
async def search_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User | None, Depends(get_opt_user)],
    q: str | None = None,
    offset: int = 0,
):
    query = (q or "").strip()
    offset = max(offset, 0)
    users = []
    has_more = False

    if query:
        result = await db.execute(
            select(User)
            .where(User.username.ilike(f"%{query}%"))
            .order_by(User.username)
            .offset(offset)
            .limit(SEARCH_LIMIT + 1)
        )
        users = list(result.scalars().all())
        has_more = len(users) > SEARCH_LIMIT
        users = users[:SEARCH_LIMIT]

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JSONResponse(
            {
                "users": [
                    {
                        "username": user.username,

                        "avatar_url": user.avatar_url,
                    }
                    for user in users
                ],
                "has_more": has_more,
                "next_offset": offset + SEARCH_LIMIT,
            }
        )

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "q": query,
            "users": users,
            "offset": offset,
            "next_offset": offset + SEARCH_LIMIT,
            "has_more": has_more,
            "title": "Поиск",
        },
    )
