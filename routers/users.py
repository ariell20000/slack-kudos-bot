#routers/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services import services
from core.dependencies import get_db, require_admin, get_current_user

router = APIRouter(tags=["Users"])

@router.get("/users/data")
def get_users_data(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return services.get_users_data(current_user, db)


@router.delete("/user/{username}")
def delete_user(username: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        services.delete_user(username, current_user, db)
        return {"detail": f"User '{username}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))