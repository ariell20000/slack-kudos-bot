#security.py

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from core.config import settings
from core.logger import logger

# Bcrypt password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    """Create a JWT access token containing `data` and an expiration.

    Args:
        data (dict): Payload data to include in the token (e.g., {'sub': username}).

    Returns:
        str: Signed JWT token.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str) -> dict | None:
    """Decode a JWT token and return its payload.

    Args:
        token (str): JWT token string.

    Returns:
        dict|None: Decoded payload on success, or None if token is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except JWTError:
        logger.warning("Invalid JWT token")
        return None


def hash_password(password: str) -> str:
    """Hash a plaintext password using the configured password context.

    Args:
        password (str): Plaintext password.

    Returns:
        str: Hashed password string.
    """

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """Verify a plaintext password against a hashed password.

    Args:
        plain_password (str): The plaintext password to verify.
        hashed_password (str): The stored hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """

    return pwd_context.verify(
        plain_password,
        hashed_password
    )