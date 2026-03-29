#routers/auth.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

import models
from models_db import User
from security import verify_password, create_access_token
from services import auth_service
from core.dependencies import get_db


router = APIRouter(tags=["Auth"])


@router.post("/register")
def register(user: models.UserCreate, db: Session = Depends(get_db)):
    """Register a new local user.

    Args:
        user (UserCreate): Pydantic model with username and password.
        db (Session): Database session injected by dependency.

    Returns:
        dict: Result from auth_service.register_user.
    """
    return auth_service.register_user(user, db)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate a user via form data and return JWT token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form containing username and password.
        db (Session): Database session.

    Returns:
        dict: {'access_token': ..., 'token_type': 'bearer'} on success.
    """
    user_data = models.UserLogin(username=form_data.username, password=form_data.password)
    return auth_service.login_user(user_data, db)
