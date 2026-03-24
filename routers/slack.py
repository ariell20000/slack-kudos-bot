#routers/slack.py

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from core.config import settings
from services.slack_service import verify_slack_signature, handle_command
from core.dependencies import get_db
from models import  SlackResponse

router = APIRouter(tags=["Slack"])

@router.post("/command", response_model=SlackResponse)
async def slack_command(request: Request, db: Session = Depends(get_db)):

    raw_body = await request.body()

    if settings.VERIFY_SLACK_SIGNATURE:
        verify_slack_signature(request.headers, raw_body)

    form = await request.form()

    return handle_command(form, db)
