#routers/kudos.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import Kudos
from models_db import User
from core.dependencies import get_current_user, get_db
from services import services

router = APIRouter(tags=["Kudos"])

@router.post("/kudos")
def add_kudos(
    kudos: Kudos,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return services.add_kudos(kudos, current_user, db)


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    return services.get_leaderboard(db)

@router.get("/kudos/mykudos")
def my_kudos_local(username: str, db: Session = Depends(get_db)):
    user = services.get_user_by_username(db, username)
    return services.get_kudos_by_username(user.username, db)

@router.get("/kudos/mystatus")
def my_status_local(username: str, db: Session = Depends(get_db)):
    return services.get_status(username, db)
