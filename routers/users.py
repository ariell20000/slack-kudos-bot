#routers/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services import services
from core.dependencies import get_db, get_current_user

router = APIRouter(tags=["Users"])

@router.get("/users/data")
def get_users_data(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Admin endpoint returning full users data including received kudos.

    Args:
        db (Session): Database session.
        current_user (User): Injected current user; must be admin.

    Returns:
        List[UserFullResponse]: All users data for admins.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return services.get_users_data(current_user, db)


@router.delete("/user/{username}")
def delete_user(username: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Admin endpoint to deactivate a user account.

    Args:
        username (str): Username to delete.
        current_user (User): Injected current user; must be admin.
        db (Session): Database session.

    Returns:
        dict: Confirmation message on success.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        services.delete_user(username, current_user, db)
        return {"detail": f"User '{username}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))