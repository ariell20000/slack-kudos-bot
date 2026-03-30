#services/user_service.py

from typing import TypedDict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.logger import logger
from models_db import User
from models import UserFullResponse
from core.dependencies import require_admin
from services.kudos_service import _convert_kudos_to_response


class StatusResponse(TypedDict):
    status: str


def get_user_by_username(username: str, db: Session) -> User:
    """Retrieve an active user by username.

    Args:
        username (str): Username to look up.
        db (Session): Database session.

    Raises:
        HTTPException: 404 if user not found, 403 if user inactive.

    Returns:
        User: The requested user model.
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return user


def _get_user_by_username_or_404(username: str, db: Session) -> User:
    """Internal helper: Get user by username or raise 404. Does NOT check is_active.

    Args:
        username (str): Username to look up.
        db (Session): Database session.

    Raises:
        HTTPException: 404 if user not found.

    Returns:
        User: The requested user model (may be inactive).
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def delete_user(username: str, current_user: User, db: Session) -> StatusResponse:
    """Soft-delete a user by setting is_active to False. Admin-only operation.

    Args:
        username (str): Username to delete.
        current_user (User): User performing the deletion (must be admin).
        db (Session): Database session.

    Raises:
        HTTPException: 404 if user not found, 403 if not admin.

    Returns:
        dict: {'status': 'deleted'} on success.
    """
    require_admin(current_user)
    
    user = _get_user_by_username_or_404(username, db)
    user.is_active = False
    logger.info("Admin %s deleted user %s", current_user.username, username)

    return {"status": "deleted"}


def get_users_data(current_user: User, db: Session) -> list[UserFullResponse]:
    """Retrieve all users in the system. Admin-only operation.

    Args:
        current_user (User): User performing the query (must be admin).
        db (Session): Database session.

    Raises:
        HTTPException: 403 if not admin.

    Returns:
        List[UserFullResponse]: List of Pydantic user response models.
    """
    require_admin(current_user)
    users = db.query(User).all()
    return [UserFullResponse(
        username=user.username,
        is_active=user.is_active,
        kudos_received=[_convert_kudos_to_response(k) for k in user.received_kudos]
    ) for user in users]


def promote_user(username: str, current_user: User, db: Session) -> StatusResponse:
    """Promote a user to admin role.

    Args:
        username (str): Username to promote.
        current_user (User): User performing the promotion (must be admin).
        db (Session): Database session.

    Raises:
        HTTPException: 404 if user not found, 403 if not admin, 400 if user inactive.

    Returns:
        dict: {'status': 'promoted'} on success.
    """
    require_admin(current_user)
    user = _get_user_by_username_or_404(username, db)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User inactive")

    user.role = "admin"
    logger.info("User %s promoted to admin", username)
    return {"status": "promoted"}
