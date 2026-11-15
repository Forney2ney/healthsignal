from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ROLE_LEVEL = {"patient": 1, "clinician": 2, "researcher": 3, "admin": 4}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except Exception:
        raise credentials_exc
    sub = payload.get("sub")
    if sub is None:
        raise credentials_exc
    user = db.scalar(select(User).where(User.email == sub))
    if user is None:
        raise credentials_exc
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{user.role}' is not permitted for this resource",
            )
        return user

    return checker


def actor_id(request: Request) -> int:
    """Best-effort actor id for audit logs (0 when unauthenticated)."""
    try:
        user = request.state.user
        return int(user.id)
    except Exception:
        return 0