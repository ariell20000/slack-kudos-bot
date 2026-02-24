from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Kudos
from models_db import User
from core.dependencies import get_current_user, get_db
import services

router = APIRouter(tags=["Kudos"])

@router.post("/kudos")
def add_kudos(
    kudos: Kudos,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return services.add_kudos(kudos, current_user, db)


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.get_leaderboard(db, current_user)
