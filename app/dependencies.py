from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.services.auth import decode_access_token


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )

    user_id = decode_access_token(access_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Invalid or expired token",
            headers={"Location": "/login"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="User not found",
            headers={"Location": "/login"},
        )

    request.state.current_user = user
    return user


async def get_opt_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User | None:
    if access_token is None:
        request.state.current_user = None
        return None

    user_id = decode_access_token(access_token)
    if user_id is None:
        request.state.current_user = None
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    request.state.current_user = user
    return user
