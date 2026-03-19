#routers/slack.py

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from services import services
from services.slack_service import verify_slack_signature
from core.dependencies import get_db
from models import Kudos, SlackResponse, UserCreate
from models_db import User
from security import verify_password, create_access_token

router = APIRouter(tags=["Slack"])

@router.post("/command", response_model=SlackResponse)
async def slack_command(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    if settings.VERIFY_SLACK_SIGNATURE:
        verify_slack_signature(request.headers, raw_body)

    form = await request.form()
    user_id = form.get("user_id")
    if not user_id:
        return SlackResponse(
            response_type="ephemeral",
            text="Missing user_id"
        )
    text = form.get("text")

    if not text:
        raise HTTPException(status_code=400, detail="Missing text")
    parts = text.strip().split()

    if not parts:
        return SlackResponse(
            response_type="ephemeral",
            text="Empty command"
        )

    command = parts[0].lower()
    args = parts[1:]

    if command == "kudos":
        return handle_kudos(user_id, args, db)

    elif command == "register":
        return handle_register(args, db)

    elif command == "users":
        return handle_users(user_id, db)

    elif command == "delete":
        return handle_delete(user_id, args, db)

    elif command == "login":
        return handle_login(args, db)

    elif command == "leaderboard":
        return handle_leaderboard(db)

    else:
        return SlackResponse(
            response_type="ephemeral",
            text=f"Unknown command: {command}"
        )

def handle_kudos(user_id, args, db):

    if len(args) < 2:
        return SlackResponse(
            response_type="ephemeral",
            text="Usage: kudos <username> <message>"
        )

    to_username = args[0]
    message = " ".join(args[1:])

    from_user = db.query(User).filter(
        User.username == user_id
    ).first()

    if not from_user:
        return SlackResponse(
            response_type="ephemeral",
            text="Unknown sender"
        )

    if not from_user.is_active:
        return SlackResponse(
            response_type="ephemeral",
            text="Sender is inactive"
        )

    to_user = db.query(User).filter(
        User.username == to_username
    ).first()

    if not to_user:
        return SlackResponse(
            response_type="ephemeral",
            text=f"User {to_username} does not exist"
        )

    if not to_user.is_active:
        return SlackResponse(
            response_type="ephemeral",
            text=f"User {to_username} is inactive"
        )

    kudos = Kudos(
        from_user=from_user.username,
        to_user=to_user.username,
        message=message
    )

    services.add_kudos(kudos, from_user, db)

    return SlackResponse(
        response_type="in_channel",
        text=f"{from_user.username} gave kudos to {to_user.username} 🎉\n\"{message}\""
    )

def handle_register(args, db):

    if len(args) < 2:
        return SlackResponse(
            response_type="ephemeral",
            text="Usage: register <username> <password>"
        )

    username = args[0]
    password = args[1]

    try:
        user = UserCreate(
            username=username,
            password=password
        )

        result = services.register_user(user, db)

        return SlackResponse(
            response_type="ephemeral",
            text=f"User {username} registered"
        )

    except Exception as e:
        return SlackResponse(
            response_type="ephemeral",
            text=str(e)
        )
def handle_users(user_id, db):

    user = db.query(User).filter(
        User.username == user_id
    ).first()

    if not user:
        return SlackResponse(
            response_type="ephemeral",
            text="Unknown user"
        )

    if user.role != "admin":
        return SlackResponse(
            response_type="ephemeral",
            text="Admin only command"
        )

    try:
        data = services.get_users_data(db, user)

        text_lines = []

        for u in data:
            text_lines.append(
                f"{u.username} | active={u.is_active} | kudos={len(u.kudos_received)}"
            )

        return SlackResponse(
            response_type="ephemeral",
            text="\n".join(text_lines)
        )

    except Exception as e:
        return SlackResponse(
            response_type="ephemeral",
            text=str(e)
        )
def handle_delete(user_id, args, db):

    if len(args) < 1:
        return SlackResponse(
            response_type="ephemeral",
            text="Usage: delete <username>"
        )

    username = args[0]

    user = db.query(User).filter(
        User.username == user_id
    ).first()

    if not user:
        return SlackResponse(
            response_type="ephemeral",
            text="Unknown user"
        )

    if user.role != "admin":
        return SlackResponse(
            response_type="ephemeral",
            text="Admin only command"
        )

    try:
        services.delete_user(username, user, db)

        return SlackResponse(
            response_type="ephemeral",
            text=f"User {username} deleted"
        )

    except Exception as e:
        return SlackResponse(
            response_type="ephemeral",
            text=str(e)
        )

def handle_login(args, db):

    if len(args) < 2:
        return SlackResponse(
            response_type="ephemeral",
            text="Usage: login <username> <password>"
        )

    username = args[0]
    password = args[1]

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        return SlackResponse(
            response_type="ephemeral",
            text="Invalid credentials"
        )


    if not verify_password(password, user.password_hash):
        return SlackResponse(
            response_type="ephemeral",
            text="Invalid credentials"
        )

    token = create_access_token({"sub": user.username})

    return SlackResponse(
        response_type="ephemeral",
        text=f"Token:\n{token}"
    )

def handle_leaderboard(db):

    try:
        data = services.get_leaderboard(db)

        if not data:
            return SlackResponse(
                response_type="in_channel",
                text="No data yet"
            )

        lines = ["🏆 Leaderboard"]

        rank = 1

        for username, count in data:
            lines.append(f"{rank}. {username} — {count}")
            rank += 1

        return SlackResponse(
            response_type="in_channel",
            text="\n".join(lines)
        )

    except Exception as e:
        return SlackResponse(
            response_type="ephemeral",
            text=str(e)
        )