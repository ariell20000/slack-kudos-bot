from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
import services
from core.dependencies import get_current_user, get_db, require_admin


router = APIRouter(tags=["Users"])

@router.get("/users/data")
def get_users_data(db: Session = Depends(get_db), admin_user=Depends(require_admin), current_user=Depends(get_current_user)):
    return services.get_users_data(db, admin_user)


@router.delete("/user/{username}")
def delete_user(username: str, db: Session = Depends(get_db), admin_user=Depends(require_admin), current_user=Depends(get_current_user)):
    return services.delete_user(username, db, admin_user)
