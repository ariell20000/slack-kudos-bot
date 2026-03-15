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

    parts = text.split(" ", 1)

    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Usage: /kudos <username> <message>"
        )

    to_username = parts[0]
    message = parts[1]

    from_user = db.query(User).filter(User.username == user_id).first()

    if not from_user or not from_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive or unknown user")

    kudos = Kudos(
        from_user=user_id,
        to_user=to_username,
        message=message
    )

    result = add_kudos(kudos, from_user, db)

    return {
        "status": "ok",
        "detail": f"Kudos sent to {to_username}",
        "kudos_id": result["kudos_id"]
    }