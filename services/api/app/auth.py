"""Auth: password hashing, JWT session cookies, and the current-user dependency.

Milestone 4a. A session is a signed JWT (HS256) carried in an httpOnly,
SameSite=Lax cookie — never localStorage. The `Secure` flag is gated on
AUTH_COOKIE_SECURE so login works over http://localhost in dev and is hardened
behind HTTPS in prod. The token carries the user id in `sub` and a 7-day `exp`;
decode verifies signature AND expiry.

`get_current_user` is the seam the RLS slice (M4b) composes with: it resolves the
authenticated user, whose id M4b will `SET LOCAL` as the Postgres session
variable inside the request transaction.
"""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import User

COOKIE_NAME = "mosaic_session"
COOKIE_PATH = "/"
COOKIE_SAMESITE = "lax"
TOKEN_TTL = timedelta(days=7)
_JWT_ALG = "HS256"

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except Argon2Error:
        return False


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + TOKEN_TTL,
    }
    return jwt.encode(payload, get_settings().auth_secret_key, algorithm=_JWT_ALG)


def _decode_token(token: str) -> int | None:
    """Return the user id if the token is valid + unexpired, else None."""
    try:
        payload = jwt.decode(
            token, get_settings().auth_secret_key, algorithms=[_JWT_ALG]
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=_create_token(user_id),
        # Max-Age aligned to the token TTL so cookie and token expire together.
        max_age=int(TOKEN_TTL.total_seconds()),
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=get_settings().auth_cookie_secure,
        path=COOKIE_PATH,
    )


def clear_session_cookie(response: Response) -> None:
    # Same name/path/samesite/secure as set, so it reliably clears.
    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        secure=get_settings().auth_cookie_secure,
        httponly=True,
    )


def get_current_user(
    request: Request, db: Session = Depends(get_session)
) -> User:
    """Resolve the authenticated user from the session cookie, or 401."""
    token = request.cookies.get(COOKIE_NAME)
    user_id = _decode_token(token) if token else None
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
