from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Subscription, User


router = APIRouter(tags=["subscriptions"])


async def get_target_user_or_404(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_followers_count(db: AsyncSession, user_id: int) -> int:
    return await db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.target_user_id == user_id)
    ) or 0


@router.post("/users/{user_id}/subscribe")
async def subscribe(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    next: Annotated[str | None, Form()] = None,
):
    target_user = await get_target_user_or_404(db, user_id)

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot subscribe to yourself",
        )

    result = await db.execute(
        select(Subscription).where(
            Subscription.subscriber_id == current_user.id,
            Subscription.target_user_id == target_user.id,
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription is None:
        db.add(
            Subscription(
                subscriber_id=current_user.id,
                target_user_id=target_user.id,
            )
        )
        await db.commit()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JSONResponse(
            {
                "is_subscribed": True,
                "followers_count": await get_followers_count(db, target_user.id),
            }
        )

    return RedirectResponse(
        next or f"/users/{target_user.username}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/{user_id}/unsubscribe")
async def unsubscribe(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    next: Annotated[str | None, Form()] = None,
):
    target_user = await get_target_user_or_404(db, user_id)

    result = await db.execute(
        select(Subscription).where(
            Subscription.subscriber_id == current_user.id,
            Subscription.target_user_id == target_user.id,
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription is not None:
        await db.delete(subscription)
        await db.commit()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JSONResponse(
            {
                "is_subscribed": False,
                "followers_count": await get_followers_count(db, target_user.id),
            }
        )

    return RedirectResponse(
        next or f"/users/{target_user.username}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
