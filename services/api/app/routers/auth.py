"""Auth endpoints (Milestone 4a): signup, login, logout, me.

Cookies are set on the injected Response. Login returns an identical 401 for
both unknown-email and wrong-password (no user enumeration); signup returns 409
on a duplicate email.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    clear_session_cookie,
    get_current_user,
    hash_password,
    set_session_cookie,
    verify_password,
)
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/auth")

MIN_PASSWORD_LEN = 8


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _user_out(user: User) -> dict:
    return {"id": user.id, "email": user.email}


@router.post("/signup")
def signup(
    body: Credentials, response: Response, db: Session = Depends(get_session)
) -> dict:
    email = _normalize_email(body.email)
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="Invalid email address")
    if len(body.password) < MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"Password must be at least {MIN_PASSWORD_LEN} characters",
        )
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    set_session_cookie(response, user.id)
    return _user_out(user)


@router.post("/login")
def login(
    body: Credentials, response: Response, db: Session = Depends(get_session)
) -> dict:
    email = _normalize_email(body.email)
    user = db.scalar(select(User).where(User.email == email))
    # Identical 401 whether the email is unknown or the password is wrong.
    if user is None or not verify_password(user.password_hash, body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_session_cookie(response, user.id)
    return _user_out(user)


@router.post("/logout")
def logout(response: Response) -> dict:
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return _user_out(user)
