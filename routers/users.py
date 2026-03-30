#routers/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models import UserFullResponse
from models_db import User
from services import user_service
from services.user_service import StatusResponse
from core.dependencies import get_db, get_current_user

router = APIRouter(tags=["Users"])

@router.get("/users/data")
def get_users_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[UserFullResponse]:
    """Admin endpoint returning full users data including received kudos.

    Args:
        db (Session): Database session.
        current_user (User): Injected current user; must be admin.

    Returns:
        List[UserFullResponse]: All users data for admins.
    """
    return user_service.get_users_data(current_user, db)


@router.delete("/user/{username}")
def delete_user(username: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StatusResponse:
    """Admin endpoint to deactivate a user account.

    Args:
        username (str): Username to delete.
        current_user (User): Injected current user; must be admin.
        db (Session): Database session.

    Returns:
        dict: Confirmation message on success.
    """
    return user_service.delete_user(username, current_user, db)