#services/auth_service.py

from typing_extensions import TypedDict
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


def _resolve_unique_username(desired_username: str, slack_id: str, db: Session) -> str:
    """Return a username guaranteed not to collide with an existing account.

    Slack's display name (user_name) is mutable and not guaranteed unique across
    users or workspaces, unlike slack_id which Slack guarantees is stable and
    unique. If the desired username is already taken (by a local account or a
    different Slack user), derive a unique one from slack_id instead of failing.

    Args:
        desired_username (str): The Slack display name to try first.
        slack_id (str): Slack user ID, used as a fallback source of uniqueness.
        db (Session): Database session.

    Returns:
        str: A username not currently used by any account.
    """
    if not db.query(User).filter(User.username == desired_username).first():
        return desired_username
    return f"{desired_username}_{slack_id[-6:]}"


def create_user(username: str, slack_id: str, db: Session) -> User:
    """Create a new Slack-authenticated user with default settings.

    Args:
        username (str): Slack display name to use as the username, if available.
        slack_id (str): Slack user ID, the account's real, stable identity.
        db (Session): Database session.

    Returns:
        User: The newly created user model.
    """
    unique_username = _resolve_unique_username(username, slack_id, db)
    if unique_username != username:
        logger.info("Slack username %s was taken, created account as %s instead", username, unique_username)

    user = User(username=unique_username, slack_id=slack_id, auth_provider="slack", role="user", is_active=True)
    db.add(user)
    db.flush()
    logger.info("User created via Slack: %s", unique_username)
    return user


def login_slack_user(slack_id: str, username: str, db: Session) -> User:
    """Authenticate or auto-register a Slack user.

    Slack's slack_id is the authoritative identity for lookup: it is unique and
    stable, unlike the display name, which is only used to seed a new account's
    username.

    Args:
        slack_id (str): Slack user ID.
        username (str): Slack display name.
        db (Session): Database session.

    Raises:
        HTTPException: 403 if user inactive.

    Returns:
        User: The authenticated or newly created user.
    """
    user = db.query(User).filter(User.slack_id == slack_id).first()

    if not user:
        logger.info("New slack user %s logging in, creating account", slack_id)
        user = create_user(username, slack_id, db)
        logger.info("Slack user %s registered successfully", slack_id)

    if not user.is_active:
        logger.warning("slack user %s tried to login but is not active", slack_id)
        raise HTTPException(status_code=403, detail="User is inactive")

    return user
