from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserLogin
from app.services.auth import create_access_token, hash_password, verify_password


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def get_safe_next(next_url: str | None) -> str | None:
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return None


def get_form_errors(error: ValidationError) -> dict[str, str]:
    errors = {}
    for item in error.errors():
        field = str(item["loc"][0]) if item["loc"] else "form"
        message = item["msg"].removeprefix("Value error, ")
        errors[field] = message
    return errors


@router.get("/register")
async def register_page(request: Request, next: str | None = None):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "next": get_safe_next(next), "errors": {}, "form_data": {}},
    )


@router.get("/register/check-username")
async def check_username(
    db: Annotated[AsyncSession, Depends(get_db)],
    username: str = "",
):
    username = username.strip()

    if len(username) < 3:
        return JSONResponse(
            {
                "available": False,
                "message": "Username должен содержать минимум 3 символа",
            }
        )

    if " " in username:
        return JSONResponse(
            {
                "available": False,
                "message": "Username не должен содержать пробелы",
            }
        )

    result = await db.execute(select(User).where(User.username == username))
    is_taken = result.scalar_one_or_none() is not None

    return JSONResponse(
        {
            "available": not is_taken,
            "message": "Username свободен" if not is_taken else "Username уже занят",
        }
    )


@router.post("/register")
async def register(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    next: Annotated[str | None, Form()] = None,
):
    safe_next = get_safe_next(next)
    form_data = {
        "username": username,
        "email": email,
        "first_name": first_name or "",
        "last_name": last_name or "",
    }

    try:
        user_data = UserCreate(
            username=username,
            email=email,
            password=password,
            first_name=first_name or None,
            last_name=last_name or None,
        )
    except ValidationError as error:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "errors": get_form_errors(error),
                "form_data": form_data,
                "next": safe_next,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    result = await db.execute(
        select(User).where(or_(User.username == user_data.username, User.email == user_data.email))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        errors = {"username": "Username уже занят"}
        if existing_user.email == user_data.email:
            errors = {"email": "Email уже зарегистрирован"}

        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "errors": errors,
                "form_data": form_data,
                "next": safe_next,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )

    db.add(user)
    await db.commit()

    if safe_next:
        return RedirectResponse(f"/login?next={quote(safe_next)}", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
async def login_page(request: Request, next: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": get_safe_next(next)},
    )


@router.post("/login")
async def login(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    login: Annotated[str, Form()],
    password: Annotated[str, Form()],
    next: Annotated[str | None, Form()] = None,
):
    safe_next = get_safe_next(next)
    try:
        login_data = UserLogin(login=login, password=password)
    except ValidationError as error:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": error.errors()[0]["msg"], "next": safe_next},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    result = await db.execute(
        select(User).where(or_(User.username == login_data.login, User.email == login_data.login))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль", "next": safe_next},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    token = create_access_token(user.id)
    response = RedirectResponse(safe_next or "/profile", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
