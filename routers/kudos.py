#routers/kudos.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models import KudosRequest, KudosResponse
from models_db import User
from core.dependencies import get_current_user, get_db
from services import kudos_service
from services.kudos_service import KudosCreatedResponse, LeaderboardEntry, UserStatsResponse

router = APIRouter(tags=["Kudos"])

@router.post("/kudos")
def add_kudos(
    kudos: KudosRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> KudosCreatedResponse:
    """Endpoint to add kudos from authenticated user.

    Args:
        kudos (KudosRequest): Pydantic model with to_user and message.
        current_user (User): Injected authenticated user (from JWT token).
        db (Session): Database session.

    Returns:
        dict: Result from kudos_service.add_kudos.
    """
    return kudos_service.add_kudos(kudos, current_user, db)


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntry]:
    """Return the leaderboard of top users.

    Args:
        limit (int): Maximum number of entries to return (1-100).
        offset (int): Number of entries to skip, for pagination.
        db (Session): Database session.

    Returns:
        List[dict]: Leaderboard data from kudos_service.get_leaderboard.
    """
    return kudos_service.get_leaderboard(db, limit=limit, offset=offset)

@router.get("/kudos/mykudos")
def my_kudos_local(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[KudosResponse]:
    """Return all kudos received by the authenticated user.

    Args:
        current_user (User): Injected authenticated user (from JWT token).
        db (Session): Database session.

    Returns:
        List[KudosResponse]: List of kudos for the user.
    """
    return kudos_service.get_kudos_by_username(current_user.username, db)

@router.get("/kudos/mystatus")
def my_status_local(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserStatsResponse:
    """Return kudos stats for the authenticated user.

    Args:
        current_user (User): Injected authenticated user (from JWT token).
        db (Session): Database session.

    Returns:
        dict: Stats returned by kudos_service.get_status.
    """
    return kudos_service.get_status(current_user.username, db)
