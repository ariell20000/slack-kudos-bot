#routers/kudos.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import Kudos
from models_db import User
from core.dependencies import get_current_user, get_db
from services import kudos_service, user_service

router = APIRouter(tags=["Kudos"])

@router.post("/kudos")
def add_kudos(
    kudos: Kudos,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint to add kudos from authenticated user.

    Args:
        kudos (Kudos): Pydantic model with kudos details.
        current_user (User): Injected authenticated user.
        db (Session): Database session.

    Returns:
        dict: Result from kudos_service.add_kudos.
    """
    return kudos_service.add_kudos(kudos, current_user, db)


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    """Return the leaderboard of top users.

    Args:
        db (Session): Database session.

    Returns:
        List[dict]: Leaderboard data from kudos_service.get_leaderboard.
    """
    return kudos_service.get_leaderboard(db)

@router.get("/kudos/mykudos")
def my_kudos_local(username: str, db: Session = Depends(get_db)):
    """Return all kudos received by a local username.

    Args:
        username (str): Username to query.
        db (Session): Database session.

    Returns:
        List[KudosResponse]: List of kudos for the user.
    """
    user = user_service.get_user_by_username(username, db)
    return kudos_service.get_kudos_by_username(user.username, db)

@router.get("/kudos/mystatus")
def my_status_local(username: str, db: Session = Depends(get_db)):
    """Return kudos stats for a local username.

    Args:
        username (str): Username to query.
        db (Session): Database session.

    Returns:
        dict: Stats returned by kudos_service.get_status.
    """
    return kudos_service.get_status(username, db)
