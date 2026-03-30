#services/__init__.py
"""Service layer for business logic.

This package contains service modules that handle business logic:
- auth_service: User authentication and registration
- user_service: User management operations  
- kudos_service: Kudos operations
- slack_service: Slack command handling
"""

from services.auth_service import (
    register_user,
    login_user,
    create_user,
    login_slack_user,
)

from services.user_service import (
    get_user_by_username,
    delete_user,
    get_users_data,
    promote_user,
)

from services.kudos_service import (
    add_kudos,
    get_kudos_by_id,
    get_kudos_by_username,
    get_leaderboard,
    get_status,
    delete_kudos_by_id,
    check_too_many_kudos_in_day,
)

__all__ = [
    # auth
    "register_user",
    "login_user", 
    "create_user",
    "login_slack_user",
    # user
    "get_user_by_username",
    "delete_user",
    "get_users_data",
    "promote_user",
    # kudos
    "add_kudos",
    "get_kudos_by_id",
    "get_kudos_by_username",
    "get_leaderboard",
    "get_status",
    "delete_kudos_by_id",
    "check_too_many_kudos_in_day",
]
