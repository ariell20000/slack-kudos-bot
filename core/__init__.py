#core/__init__.py
"""Core utilities: config, dependencies, logging."""

from core.config import settings
from core.dependencies import get_db, get_current_user, require_admin
from core.logger import logger

__all__ = [
    "settings",
    "get_db",
    "get_current_user",
    "require_admin",
    "logger",
]
