# slack.py

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from services.slack_service import verify_slack_signature
from services.services import add_kudos
from core.dependencies import get_db
from models import Kudos
from models_db import User
router = APIRouter(tags=["Slack"])

@router.post("/command")
async def slack_command(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    # verify_slack_signature(request.headers, raw_body)

    form = await request.form()
    user_id = form.get("user_id")
    text = form.get("text")

    if not text:
        raise HTTPException(status_code=400, detail="Missing text")

    parts = text.strip().split(" ", 1)
    if len(parts) < 2 or not parts[0] or not parts[1].strip():
        raise HTTPException(
            status_code=400,
            detail="Usage: /kudos <username> <message>. Make sure both are non-empty."
        )

    to_username = parts[0].strip()
    message = parts[1].strip()

    # Validate sender
    from_user = db.query(User).filter(User.username == user_id).first()
    if not from_user:
        raise HTTPException(status_code=400, detail=f"Unknown sender: {user_id}")
    if not from_user.is_active:
        raise HTTPException(status_code=403, detail="Sender is inactive")

    # Validate recipient
    to_user = db.query(User).filter(User.username == to_username).first()
    if not to_user:
        raise HTTPException(status_code=400, detail=f"Recipient user {to_username} does not exist")
    if not to_user.is_active:
        raise HTTPException(status_code=403, detail=f"Recipient user {to_username} is inactive")

    # Create Kudos with real user IDs
    kudos = Kudos(
        from_user=from_user.username,
        to_user=to_user.username,
        message=message
    )

    result = add_kudos(kudos, from_user, db)

    return {
        "status": "ok",
        "detail": f"Kudos sent to {to_user.username}",
        "kudos_id": result["kudos_id"]
    }