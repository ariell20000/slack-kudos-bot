# tests/test_slack_service.py

import os
import sys
import hmac
import hashlib
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from models import KudosRequest
from services import slack_service


CURRENT_TIMESTAMP = 1_700_000_000


def _make_slack_signature(secret: str, timestamp: str, body: bytes) -> str:
    basestring = f"v0:{timestamp}:{body.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), basestring, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def test_valid_slack_signature_is_accepted(monkeypatch):
    monkeypatch.setattr(slack_service, "time", lambda: CURRENT_TIMESTAMP)
    monkeypatch.setattr(settings, "SLACK_SIGNING_SECRET", "signing-secret")

    timestamp = str(CURRENT_TIMESTAMP)
    body = b"token=abc&text=hello"
    headers = {
        "X-Slack-Signature": _make_slack_signature("signing-secret", timestamp, body),
        "X-Slack-Request-Timestamp": timestamp,
    }

    assert slack_service.verify_slack_signature(headers, body) is True


def test_missing_slack_headers_are_rejected_with_bad_request():
    with pytest.raises(HTTPException) as excinfo:
        slack_service.verify_slack_signature({}, b"payload")

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Missing Slack headers"


def test_request_older_than_five_minutes_is_rejected(monkeypatch):
    monkeypatch.setattr(slack_service, "time", lambda: 2000)
    monkeypatch.setattr(settings, "SLACK_SIGNING_SECRET", "signing-secret")

    body = b"token=abc"
    headers = {
        "X-Slack-Signature": _make_slack_signature("signing-secret", "1000", body),
        "X-Slack-Request-Timestamp": "1000",
    }

    with pytest.raises(HTTPException) as excinfo:
        slack_service.verify_slack_signature(headers, body)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Request too old"


def test_invalid_slack_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(slack_service, "time", lambda: CURRENT_TIMESTAMP)
    monkeypatch.setattr(settings, "SLACK_SIGNING_SECRET", "signing-secret")

    body = b"token=abc"
    headers = {
        "X-Slack-Signature": "v0=invalid-signature",
        "X-Slack-Request-Timestamp": str(CURRENT_TIMESTAMP),
    }

    with pytest.raises(HTTPException) as excinfo:
        slack_service.verify_slack_signature(headers, body)

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Invalid Slack signature"


def test_error_response_uses_ephemeral_format():
    response = slack_service.error_response("Something went wrong")

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "❌ Something went wrong"


def test_success_response_uses_ephemeral_format():
    response = slack_service.success_response("All good")

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "✅ All good"


def test_missing_slack_id_returns_error_response(db_session):
    response = slack_service.handle_command(
        {"user_name": "alice", "command": "/kudos", "text": "bob great job"},
        db_session,
    )

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "❌ Missing slack_id"


def test_unknown_command_returns_error_response(db_session):
    response = slack_service.handle_command(
        {"user_id": "U123", "user_name": "alice", "command": "/does-not-exist", "text": ""},
        db_session,
    )

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "❌ Unknown command: does-not-exist"


def test_kudos_command_is_dispatched_to_the_kudos_handler(monkeypatch, db_session):
    captured = {}

    def fake_handle_kudos(slack_id, username, args, db):
        captured["slack_id"] = slack_id
        captured["username"] = username
        captured["args"] = args
        captured["db"] = db
        return {"response_type": "ephemeral", "blocks": []}

    monkeypatch.setattr(slack_service, "handle_kudos", fake_handle_kudos)

    response = slack_service.handle_command(
        {
            "user_id": "U123",
            "user_name": "alice",
            "command": "/KUDOS",
            "text": "bob great job",
        },
        db_session,
    )

    assert response["response_type"] == "ephemeral"
    assert captured["slack_id"] == "U123"
    assert captured["username"] == "alice"
    assert captured["args"] == ["bob", "great", "job"]
    assert captured["db"] is db_session


def test_help_command_returns_command_list(db_session):
    response = slack_service.handle_command(
        {"user_id": "U123", "user_name": "alice", "command": "/help", "text": ""},
        db_session,
    )

    assert response["response_type"] == "ephemeral"
    text = response["blocks"][0]["text"]["text"]
    assert "/kudos user message" in text
    assert "/promote user (admin)" in text


def test_leaderboard_command_returns_no_data_message_when_there_are_no_scores(monkeypatch, db_session):
    monkeypatch.setattr(slack_service.services, "get_leaderboard", lambda db: [])

    response = slack_service.handle_leaderboard(db_session)

    assert response["response_type"] == "in_channel"
    assert response["blocks"][0]["text"]["text"] == "No data yet"


def test_delete_command_requires_a_username_argument(db_session):
    response = slack_service.handle_delete("U123", [], db_session, "alice")

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "❌ Usage: delete <username>"


def test_mykudos_command_returns_no_kudos_message_when_user_has_none(monkeypatch, db_session):
    monkeypatch.setattr(
        slack_service.services,
        "login_slack_user",
        lambda db, slack_id, username: SimpleNamespace(username=username),
    )
    monkeypatch.setattr(slack_service.services, "get_kudos_by_username", lambda username, db: [])

    response = slack_service.handle_mykudos("U123", db_session, "alice")

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "✅ No kudos yet"


def test_promote_command_requires_a_username_argument(db_session):
    response = slack_service.handle_promote("U123", [], db_session, "alice")

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "❌ Usage: promote <username>"


def test_users_command_returns_error_message_when_login_fails(monkeypatch, db_session):
    def fake_login_slack_user(slack_id, username, db):
        raise Exception("not allowed")

    monkeypatch.setattr(slack_service.services, "login_slack_user", fake_login_slack_user)

    response = slack_service.handle_users("U123", db_session, "alice")

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "❌ not allowed"


def test_kudos_handler_returns_success_message_when_kudos_is_created(monkeypatch, db_session):
    captured = {}

    def fake_login_slack_user(slack_id, username, db):
        return SimpleNamespace(username=username)

    def fake_add_kudos(form, from_user, db):
        captured["form"] = form
        captured["from_user"] = from_user
        captured["db"] = db
        return {"status": "received", "kudos_id": 1}

    monkeypatch.setattr(slack_service.services, "login_slack_user", fake_login_slack_user)
    monkeypatch.setattr(slack_service.services, "add_kudos", fake_add_kudos)

    response = slack_service.handle_kudos(
        "U123",
        "alice",
        KudosRequest(to_user="bob", message="great job"),
        db_session,
    )

    assert response["response_type"] == "ephemeral"
    assert response["blocks"][0]["text"]["text"] == "✅ Kudos sent from alice to bob"
    assert captured["form"].to_user == "bob"
    assert captured["form"].message == "great job"
    assert captured["from_user"].username == "alice"
    assert captured["db"] is db_session
