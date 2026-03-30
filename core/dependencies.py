#core/dependencies.py

from typing import Generator
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import SessionLocal
from models_db import User
from core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session with automatic transaction management.

    The session auto-commits on successful request completion and auto-rollbacks
    on any exception, ensuring atomic request-level transactions.

    Yields:
        Session: SQLAlchemy session bound to the application's engine.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency that decodes an access token and returns the corresponding User.

    Args:
        token (str): JWT token provided by OAuth2PasswordBearer dependency.
        db (Session): Database session injected by Depends(get_db).

    Raises:
        HTTPException: 401 if token is invalid or user not found.

    Returns:
        User: The authenticated user model instance.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that enforces admin privileges.

    Args:
        current_user (User): Injected current user via get_current_user.

    Raises:
        HTTPException: 403 if the current user is not an admin.

    Returns:
        User: The current_user if they have admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
