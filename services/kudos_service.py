#services/kudos_service.py

from typing import TypedDict
from sqlalchemy import func
from sqlalchemy.orm import joinedload, Session
from fastapi import HTTPException
from datetime import datetime, timezone

from core.logger import logger
from core.config import settings
from models_db import KudosDB, User
from models import KudosResponse, Kudos, KudosRequest
from core.dependencies import require_admin


class StatusResponse(TypedDict):
    status: str


class KudosCreatedResponse(TypedDict):
    status: str
    kudos_id: int


class LeaderboardEntry(TypedDict):
    username: str
    score: int


class UserStatsResponse(TypedDict):
    username: str
    kudos_given: int
    kudos_received: int
    is_active: bool


def _convert_kudos_to_response(kudos_db: KudosDB) -> KudosResponse:
    """Convert a KudosDB ORM object to a KudosResponse Pydantic model.

    Args:
        kudos_db (KudosDB): ORM kudos model from database.

    Returns:
        KudosResponse: Pydantic model with formatted data.
    """
    return KudosResponse(
        message=kudos_db.message,
        from_user=kudos_db.from_user.username,
        time_created=kudos_db.time_created
    )


def get_leaderboard(db: Session) -> list[LeaderboardEntry]:
    """Retrieve a leaderboard of users ranked by kudos received.

    Args:
        db (Session): Database session.

    Returns:
        list: List of dicts with 'username' and 'score'.
    """
    leaderboard = (
        db.query(User.username, func.count(KudosDB.id).label("score"))
        .outerjoin(KudosDB, User.id == KudosDB.to_user_id)
        .group_by(User.username)
        .order_by(func.count(KudosDB.id).desc())
        .all()
    )
    return [{"username": username, "score": count} for username, count in leaderboard]


def get_kudos_by_id(kudos_id: int, db: Session) -> KudosResponse:
    """Retrieve a single kudos entry by ID.

    Args:
        kudos_id (int): ID of the kudos entry.
        db (Session): Database session.

    Raises:
        HTTPException: 404 if kudos not found.

    Returns:
        KudosResponse: Pydantic kudos response model.
    """
    kudos = db.query(KudosDB).options(joinedload(KudosDB.from_user), joinedload(KudosDB.to_user)).filter(KudosDB.id == kudos_id).first()
    if not kudos:
        raise HTTPException(status_code=404, detail="Kudos not found")
    return _convert_kudos_to_response(kudos)


def delete_kudos_by_id(kudos_id: int, current_user: User, db: Session) -> StatusResponse:
    """Delete a kudos entry by ID. Admin-only operation.

    Args:
        kudos_id (int): ID of the kudos entry to delete.
        current_user (User): User performing the deletion (must be admin).
        db (Session): Database session.

    Raises:
        HTTPException: 404 if kudos not found, 403 if not admin, 500 on DB error.

    Returns:
        dict: {'status': 'deleted'} on success.
    """
    require_admin(current_user)

    kudos = db.query(KudosDB).filter(KudosDB.id == kudos_id).first()
    if not kudos:
        logger.warning("Admin %s tried to delete kudos_id %d but kudos not found", current_user.username, kudos_id)
        raise HTTPException(status_code=404, detail="Kudos not found")

    db.delete(kudos)
    logger.info("Admin %s deleted kudos_id %d", current_user.username, kudos_id)
    return {"status": "deleted"}


def get_kudos_by_username(username: str, db: Session) -> list[KudosResponse]:
    """Retrieve all kudos received by a specific user.

    Args:
        username (str): Username to retrieve kudos for.
        db (Session): Database session.

    Raises:
        HTTPException: 404 if user not found.

    Returns:
        List[KudosResponse]: List of Pydantic kudos response models.
    """
    from services.user_service import _get_user_by_username_or_404
    user = _get_user_by_username_or_404(username, db)
    kudos = user.received_kudos
    return [_convert_kudos_to_response(k) for k in kudos]


def add_kudos(kudos_request: KudosRequest, from_user: User, db: Session) -> KudosCreatedResponse:
    """Create a new kudos entry from one user to another.

    Args:
        kudos_request (KudosRequest): Pydantic model with to_user and message.
        from_user (User): User giving the kudos.
        db (Session): Database session.

    Raises:
        HTTPException: Various errors for validation failures or business rule violations.

    Returns:
        dict: {'status': 'received', 'kudos_id': int} on success.
    """
    from services.user_service import _get_user_by_username_or_404
    
    if len(kudos_request.message) > settings.MAX_KUDOS_MESSAGE_LENGTH:
        logger.warning("Sender %s tried to send kudos with message too long", from_user.username)
        raise HTTPException(status_code=400, detail="Message too long")

    if from_user.username == kudos_request.to_user:
        logger.warning("Sender %s tried to send kudos to self", from_user.username)
        raise HTTPException(status_code=400, detail="You cannot give kudos to yourself")

    to_user = _get_user_by_username_or_404(kudos_request.to_user, db)

    if not from_user.is_active:
        logger.warning("Inactive sender %s tried to send kudos", from_user.username)
        raise HTTPException(status_code=400, detail="Sender is inactive")

    if not to_user.is_active:
        logger.warning("Sender %s tried to send kudos to inactive user %s", from_user.username, to_user.username)
        raise HTTPException(status_code=400, detail="Receiver is inactive")

    if check_too_many_kudos_in_day(db, from_user.id):
        logger.warning("Sender %s reached daily kudos limit", from_user.username)
        raise HTTPException(status_code=400, detail="Too many kudos today")

    kudos = KudosDB(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        message=kudos_request.message,
        time_created=datetime.now(timezone.utc)
    )
    db.add(kudos)
    db.flush()
    logger.info("Kudos created from %s to %s", from_user.username, to_user.username)
    return {"status": "received", "kudos_id": kudos.id}


def get_status(username: str, db: Session) -> UserStatsResponse:
    """Retrieve statistics for a specific user (kudos given/received).

    Args:
        username (str): Username to retrieve stats for.
        db (Session): Database session.

    Raises:
        HTTPException: 404 if user not found.

    Returns:
        dict: Statistics including kudos_given, kudos_received, and is_active.
    """
    from services.user_service import _get_user_by_username_or_404
    user = _get_user_by_username_or_404(username, db)
    kudos_given = db.query(KudosDB).filter(KudosDB.from_user_id == user.id).count()
    kudos_received = db.query(KudosDB).filter(KudosDB.to_user_id == user.id).count()
    return {
        "username": username,
        "kudos_given": kudos_given,
        "kudos_received": kudos_received,
        "is_active": user.is_active
    }


def check_too_many_kudos_in_day(db: Session, user_id: int, limit: int | None = None) -> bool:
    """Check if a user has exceeded their daily kudos limit.

    Args:
        db (Session): Database session.
        user_id (int): User ID to check.
        limit (int, optional): Override limit (defaults to settings.DAILY_KUDOS_LIMIT).

    Returns:
        bool: True if user has reached/exceeded limit, False otherwise.
    """
    if limit is None:
        limit = settings.DAILY_KUDOS_LIMIT

    # Use date range for better index performance (avoids func.date() on column)
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    
    kudos_count = db.query(KudosDB).filter(
        KudosDB.from_user_id == user_id,
        KudosDB.time_created >= start_of_day
    ).count()

    return kudos_count >= limit
