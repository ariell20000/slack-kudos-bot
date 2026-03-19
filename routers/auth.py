#routers/auth.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

import models
from models_db import User
from security import verify_password, create_access_token
from services import services
from core.dependencies import get_db


router = APIRouter(tags=["Auth"])


@router.post("/register")
def register(user: models.UserCreate, db: Session = Depends(get_db)):
    return services.register_user(user, db)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        {"sub": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
