# services/slack_service.py

import hmac
import hashlib
from time import time
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from models import SlackResponse, UserCreate, Kudos
from models_db import User
from core.config import settings
from security import verify_password, create_access_token
from services import services


def verify_slack_signature(headers, body: bytes):
    slack_signature = headers.get("X-Slack-Signature")
    slack_timestamp = headers.get("X-Slack-Request-Timestamp")

    if not slack_signature or not slack_timestamp:
        raise HTTPException(status_code=400, detail="Missing Slack headers")

    if abs(time() - int(slack_timestamp)) > 60 * 5:
        raise HTTPException(status_code=400, detail="Request too old")

    basestring = f"v0:{slack_timestamp}:{body.decode('utf-8')}".encode("utf-8")

    computed_signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode("utf-8"),
        basestring,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, slack_signature):
        raise HTTPException(status_code=403, detail="Invalid Slack signature")

    return True


def handle_command(form, db: Session):
    slack_id = form.get("user_id")
    username = form.get("user_name")

    if not slack_id:
        return error_response("Missing slack_id")

    command = form.get("command", "").lstrip("/").lower()
    args = form.get("text", "").split()

    if command == "kudos":
        return handle_kudos(slack_id, username, args, db)
    elif command == "register":
        return handle_register(args, db)
    elif command == "users":
        return handle_users(slack_id, db)
    elif command == "delete":
        return handle_delete(slack_id, args, db)
    elif command == "leaderboard":
        return handle_leaderboard(db)
    elif command == "mystatus":
        return handle_status(slack_id, db)
    elif command == "mykudos":
        return handle_mykudos(slack_id, db)
    elif command == "help":
        return handle_help()
    elif command == "promote":
        return handle_promote(slack_id, args, db)
    else:
        return error_response(f"Unknown command: {command}")


# ---------------- Block Kit helpers ----------------

def error_response(message: str):
    return {
        "response_type": "ephemeral",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"❌ {message}"}}
        ]
    }


def success_response(message: str):
    return {
        "response_type": "ephemeral",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"✅ {message}"}}
        ]
    }


# ---------------- Command handlers ----------------

def handle_kudos(slack_id, username, args, db):
    if len(args) < 2:
        return error_response("Usage: kudos <username> <message>")

    to_username = args[0]
    message = " ".join(args[1:])
    from_user = services.login_slack_user(db, slack_id, username)

    if not from_user.is_active:
        return error_response("Sender is inactive")

    if from_user.username == to_username:
        return error_response("You cannot give kudos to yourself")

    try:
        to_user = services.get_user_by_username(db, to_username)
    except Exception as e:
        return error_response(str(e))

    kudos = Kudos(
        from_user=from_user.username,
        to_user=to_user.username,
        message=message,
    )

    services.add_kudos(kudos, from_user, db)

    return {
        "response_type": "ephemeral",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Kudos sent from {from_user.username} to {to_user.username} 🎉"
                }
            }
        ]
    }

def handle_register(args, db):
    if len(args) < 2:
        return error_response("Usage: register <username> <password>")

    username = args[0]
    password = args[1]

    try:
        user = UserCreate(username=username, password=password)
        services.register_user(user, db)
        return success_response(f"User *{username}* registered successfully!")
    except Exception as e:
        return error_response(str(e))


def handle_users(slack_id, db):
    user = db.query(User).filter(User.slack_id == slack_id).first()

    if not user:
        return error_response("Unknown user")

    if user.role != "admin":
        return error_response("Admin only command")

    try:
        data = services.get_users_data(user, db)

        lines = [
            f"{u.username} | active={u.is_active} | kudos={len(u.kudos_received)}"
            for u in data
        ]

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


def handle_delete(slack_id, args, db):

    if len(args) < 1:
        return error_response("Usage: delete <username>")

    username = args[0]

    user = db.query(User).filter(User.slack_id == slack_id).first()

    if not user:
        return error_response("Unknown user")

    if user.role != "admin":
        return error_response("Admin only command")

    try:
        services.delete_user(username, user, db)

        return success_response(f"User *{username}* deleted")

    except Exception as e:
        return error_response(str(e))


def handle_login(args, db):
    if len(args) < 2:
        return error_response("Usage: login <username> <password>")

    username = args[0]
    password = args[1]

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return error_response("Invalid credentials")

    token = create_access_token({"sub": user.username})

    return {
        "response_type": "ephemeral",
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "🔑 Login successful."}},
            {"type": "context", "elements": [{"type": "plain_text", "text": f"Token: {token}", "emoji": True}]}
        ]
    }

def handle_leaderboard(db):
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
def handle_status(slack_id, db):

    user = db.query(User).filter(User.slack_id == slack_id).first()

    if not user:
        return error_response("Unknown user")

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

def handle_mykudos(slack_id, db):

    user = db.query(User).filter(User.slack_id == slack_id).first()

    if not user:
        return error_response("Unknown user")

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
def handle_promote(slack_id, args, db):

    if len(args) < 1:
        return error_response("Usage: promote <username>")

    username = args[0]

    admin = db.query(User).filter(User.slack_id == slack_id).first()

    if not admin:
        return error_response("Unknown user")

    if admin.role != "admin":
        return error_response("Admin only")

    try:
        services.promote_user(username, db)

        return success_response(f"{username} promoted to admin")

    except Exception as e:
        return error_response(str(e))