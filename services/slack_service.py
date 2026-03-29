# services/slack_service.py

import hmac
import hashlib
from time import time
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.logger import logger
from models import Kudos, KudosRequest
from core.config import settings
from services import services


def verify_slack_signature(headers, body: bytes):
    """Verify Slack request signature and timestamp.

    Args:
        headers (Mapping): Request headers containing Slack signature and timestamp.
        body (bytes): Raw request body bytes.

    Raises:
        HTTPException: 400 if headers are missing or request is too old; 403 if signature invalid.

    Returns:
        bool: True if verification succeeds.
    """
    slack_signature = headers.get("X-Slack-Signature")
    slack_timestamp = headers.get("X-Slack-Request-Timestamp")

    if not slack_signature or not slack_timestamp:
        logger.warning("failed to verify slack signature")
        raise HTTPException(status_code=400, detail="Missing Slack headers")

    if abs(time() - int(slack_timestamp)) > 60 * 5:
        logger.warning("failed to verify slack signature because request timed out")
        raise HTTPException(status_code=400, detail="Request too old")

    basestring = f"v0:{slack_timestamp}:{body.decode('utf-8')}".encode("utf-8")

    computed_signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode("utf-8"),
        basestring,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, slack_signature):
        logger.warning("failed to verify slack signature because invalid slack signature")
        raise HTTPException(status_code=403, detail="Invalid Slack signature")

    return True


def handle_command(form, db: Session):
    """Dispatch a Slack form payload to the appropriate command handler.

    Args:
        form (Mapping): Parsed form data from Slack (user_id, command, text, etc.).
        db (Session): Database session.

    Returns:
        dict: Block Kit formatted response.
    """
    slack_id = form.get("user_id")
    username = form.get("user_name")

    if not slack_id:
        return error_response("Missing slack_id")

    command = form.get("command", "").lstrip("/").lower()
    args = form.get("text", "").split()

    if command == "kudos":
        return handle_kudos(slack_id, username, args, db)
    elif command == "users":
        return handle_users(slack_id, db, username)
    elif command == "delete":
        return handle_delete(slack_id, args, db, username)
    elif command == "leaderboard":
        return handle_leaderboard(db)
    elif command == "mystatus":
        return handle_status(slack_id, db, username)
    elif command == "mykudos":
        return handle_mykudos(slack_id, db, username)
    elif command == "help":
        return handle_help()
    elif command == "promote":
        return handle_promote(slack_id, args, db, username)
    else:
        return error_response(f"Unknown command: {command}")


# ---------------- Block Kit helpers ----------------

def error_response(message: str):
    """Return a Slack Block Kit ephemeral error response.

    Args:
        message (str): Error message to display.

    Returns:
        dict: Block Kit formatted ephemeral error response.
    """
    return {
        "response_type": "ephemeral",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"❌ {message}"}}
        ]
    }


def success_response(message: str):
    """Return a Slack Block Kit ephemeral success response.

    Args:
        message (str): Success message to display.

    Returns:
        dict: Block Kit formatted ephemeral success response.
    """
    return {
        "response_type": "ephemeral",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"✅ {message}"}}
        ]
    }


# ---------------- Command handlers ----------------

def handle_kudos(slack_id, username, form: KudosRequest, db):
    """Handle the /kudos Slack command: ensure Slack user exists and add kudos.

    Args:
        slack_id (str): Slack user ID of the sender.
        username (str): Slack display name of the sender.
        form (KudosRequest): Parsed kudos request payload.
        db (Session): Database session.

    Returns:
        dict: Block Kit success response.
    """
    from_user = services.login_slack_user(db, slack_id, username)
    services.add_kudos(form, from_user, db)
    return success_response(f"Kudos sent from {from_user.username} to {form.to_user}")


def handle_users(slack_id, db, username):
    """Handle the /users Slack command (admin-only): return users summary.

    Args:
        slack_id (str): Slack user ID of the requester.
        db (Session): Database session.
        username (str): Slack display name.

    Returns:
        dict: Block Kit response with users summary or an error response.
    """
    try:
        user = services.login_slack_user(db, slack_id, username)
    except Exception as e:
        return error_response(str(e))
    try:
        data = services.get_users_data(user, db)

        lines = [
            f"{u.username} | active={u.is_active} | kudos={len(u.kudos_received)}"
            for u in data
        ]
        logger.info("slack command: user %s got users data", username)
        return {
            "response_type": "ephemeral",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "\n".join(lines),
                    },
                }
            ],
        }

    except Exception as e:
        return error_response(str(e))


def handle_delete(slack_id, args, db, sender_name):
    """Handle the /delete Slack command (admin-only): deactivate a user.

    Args:
        slack_id (str): Slack user ID of the requester.
        args (list): Command arguments (expects username as first arg).
        db (Session): Database session.
        sender_name (str): Slack display name of the requester.

    Returns:
        dict: Success or error Block Kit response.
    """

    if len(args) < 1:
        return error_response("Usage: delete <username>")

    username = args[0]

    try:
        user = services.login_slack_user(db, slack_id, sender_name)
    except Exception as e:
        return error_response(str(e))
    try:
        services.delete_user(username, user, db)
        logger.info("slack command: user %s deleted user %s", user.username, username)
        return success_response(f"User *{username}* deleted")

    except Exception as e:
        return error_response(str(e))


def handle_leaderboard(db):
    """Handle the /leaderboard Slack command and format the leaderboard for Slack.

    Args:
        db (Session): Database session.

    Returns:
        dict: Block Kit formatted leaderboard or a message indicating no data.
    """
    try:
        data = services.get_leaderboard(db)
        if not data:
            return {"response_type": "in_channel",
                    "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "No data yet"}}]}

        blocks = [{"type": "header", "text": {"type": "plain_text", "text": "🏆 Leaderboard", "emoji": True}}]

        for rank, item in enumerate(data, start=1):
            username = item["username"]
            count = item["score"]
            emoji = "🔥" if rank == 1 else "🥇" if rank == 2 else "🥈" if rank == 3 else "🥉" if rank == 4 else ""
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{emoji} *{rank}. {username}* — {count} kudos"}
            })
        return {"response_type": "in_channel", "blocks": blocks}
    except Exception as e:
        return error_response(str(e))

def handle_status(slack_id, db, username):
    """Handle the /mystatus Slack command and return user stats.

    Args:
        slack_id (str): Slack user ID of the requester.
        db (Session): Database session.
        username (str): Slack display name.

    Returns:
        dict: Block Kit formatted ephemeral response with user stats.
    """
    try:
        user = services.login_slack_user(db, slack_id, username)
    except Exception as e:
        return error_response(str(e))

    try:
        data = services.get_status(user.username, db)

        text = (
            f"*User:* {data['username']}\n"
            f"Kudos given: {data['kudos_given']}\n"
            f"Kudos received: {data['kudos_received']}\n"
            f"Active: {data['is_active']}"
        )

        return {
            "response_type": "ephemeral",
            "blocks": [
                {"type": "section",
                 "text": {"type": "mrkdwn", "text": text}}
            ]
        }

    except Exception as e:
        return error_response(str(e))

def handle_mykudos(slack_id, db, username):
    """Handle the /mykudos Slack command and return kudos sent to the user.

    Args:
        slack_id (str): Slack user ID of the requester.
        db (Session): Database session.
        username (str): Slack display name.

    Returns:
        dict: Block Kit formatted ephemeral response with the user's kudos list.
    """
    try:
        user = services.login_slack_user(db, slack_id, username)
    except Exception as e:
        return error_response(str(e))

    try:
        kudos = services.get_kudos_by_username(user.username, db)

        if not kudos:
            return success_response("No kudos yet")

        lines = [
            f"{k.from_user} → {k.message}"
            for k in kudos
        ]

        return {
            "response_type": "ephemeral",
            "blocks": [
                {"type": "section",
                 "text": {"type": "mrkdwn",
                          "text": "\n".join(lines)}}
            ]
        }

    except Exception as e:
        return error_response(str(e))

def handle_help():
    """Return the help text describing available Slack commands.

    Returns:
        dict: Block Kit ephemeral response with command list.
    """

    text = (
        "*Available commands:*\n"
        "/kudos user message\n"
        "/mystatus\n"
        "/mykudos\n"
        "/leaderboard\n"
        "/login user pass\n"
        "/register user pass\n"
        "/users (admin)\n"
        "/delete user (admin)\n"
        "/promote user (admin)"
    )

    return {
        "response_type": "ephemeral",
        "blocks": [
            {"type": "section",
             "text": {"type": "mrkdwn", "text": text}}
        ]
    }
def handle_promote(slack_id, args, db, sender_name):

    if len(args) < 1:
        return error_response("Usage: promote <username>")

    username = args[0]

    try:
        admin = services.login_slack_user(db, slack_id, sender_name)
    except Exception as e:
        return error_response(str(e))

    try:
        services.promote_user(username,admin, db)
        logger.info("slack command: user %s promoted user %s to admin", sender_name, username)

        return success_response(f"{username} promoted to admin")

    except Exception as e:
        return error_response(str(e))