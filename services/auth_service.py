#services/auth_service.py

from typing import TypedDict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.logger import logger
from models_db import User
from models import UserCreate, UserLogin
from core.security import hash_password, verify_password, create_access_token


class StatusResponse(TypedDict):
    status: str


class TokenResponse(TypedDict):
    access_token: str
    token_type: str


def register_user(user_data: UserCreate, db: Session) -> StatusResponse:
    """Register a new local auth user.

    Args:
        user_data: Pydantic model with username and password.
        db (Session): Database session.

    Raises:
        HTTPException: 400 if username exists, 500 on database error.

    Returns:
        dict: {'status': 'created'} on success.
    """
    user = db.query(User).filter(User.username == user_data.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        password_hash=hashed,
        auth_provider="local",
        role="user",
        is_active=True,
    )
    db.add(new_user)
    logger.info("User registered: %s", user_data.username)

    return {"status": "created"}


def login_user(user_data: UserLogin, db: Session) -> TokenResponse:
    """Authenticate a local user and return an access token.

    Args:
        user_data: Pydantic model with username and password.
        db (Session): Database session.

    Raises:
        HTTPException: 401 for invalid credentials or 403 if user inactive.

    Returns:
        dict: Access token payload with 'access_token' and 'token_type'.
    """
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user:
        logger.warning("Login failed for non existing user - %s", user_data.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.auth_provider != "local":
        logger.warning("Login attempt for slack user - %s", user_data.username)
        raise HTTPException(status_code=400, detail="Use Slack login")

    if not user.is_active:
        logger.warning("Login failed for non active user - %s", user_data.username)
        raise HTTPException(status_code=403, detail="User is inactive")

    if not verify_password(user_data.password, user.password_hash):
        logger.warning("Login failed for user %s - incorrect password", user_data.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})
    logger.info("User logged in: %s", user_data.username)

    return {"access_token": access_token, "token_type": "bearer"}


def create_user(username: str, db: Session) -> User:
    """Create a new Slack-authenticated user with default settings.

    Args:
        username (str): Username for the new user.
        db (Session): Database session.

    Returns:
        User: The newly created user model.
    """
    user = User(username=username, auth_provider="slack", role="user", is_active=True)
    db.add(user)
    db.flush()
    logger.info("User created via Slack: %s", username)
    return user


def login_slack_user(slack_id: str, username: str, db: Session) -> User:
    """Authenticate or auto-register a Slack user.

    Args:
        slack_id (str): Slack user ID.
        username (str): Slack username.
        db (Session): Database session.

    Raises:
        HTTPException: 403 if user inactive.

    Returns:
        User: The authenticated or newly created user.
    """
    user = db.query(User).filter(User.slack_id == slack_id).first()

    if not user:
        logger.info("New slack user %s logging in, creating account", slack_id)
        user = create_user(username, db)
        user.slack_id = slack_id
        logger.info("Slack user %s registered successfully", slack_id)

    if not user.is_active:
        logger.warning("slack user %s tried to login but is not active", slack_id)
        raise HTTPException(status_code=403, detail="User is inactive")

    return user
