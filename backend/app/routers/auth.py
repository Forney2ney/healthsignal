import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..deps import get_current_user
from ..models import AuditLog, User
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="email already registered")
    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.add(AuditLog(
        actor_user_id=user.id, action="auth.register",
        detail_json=json.dumps({"role": body.role}),
    ))
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.email, role=user.role)
    return schemas.TokenOut(access_token=token, role=user.role, email=user.email)


@router.post("/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid email or password")
    token = create_access_token(subject=user.email, role=user.role)
    return schemas.TokenOut(access_token=token, role=user.role, email=user.email)


@router.get("/me", response_model=schemas.UserOut)
def me(user: User = Depends(get_current_user)):
    return user