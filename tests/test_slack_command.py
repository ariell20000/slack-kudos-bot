import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from models_db import User
from routers.slack import router as slack_router
from core.dependencies import get_db


# ----------------------------
# Fixtures
# ----------------------------
@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(slack_router)
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def users(db_session):
    active_sender = User(username="alice", password_hash="hashed", role="user", is_active=True)
    inactive_sender = User(username="bob", password_hash="hashed", role="user", is_active=False)
    recipient = User(username="charlie", password_hash="hashed", role="user", is_active=True)
    db_session.add_all([active_sender, inactive_sender, recipient])
    db_session.commit()
    return active_sender, inactive_sender, recipient

# ----------------------------
# Helper to get text from blocks
# ----------------------------
def get_text_from_block(response_data):
    if "blocks" in response_data and response_data["blocks"]:
        block = response_data["blocks"][0]
        if "text" in block and "text" in block["text"]:
            return block["text"]["text"]
    return ""


# ----------------------------
# Tests
# ----------------------------
def test_recipient_not_exist(client, users):
    sender, _, _ = users

    response = client.post(
        "/command",
        data={
            "user_id": sender.username,
            "text": "kudos nonexistent_user Hello"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["response_type"] == "ephemeral"
    text_content = get_text_from_block(data)
    assert "does not exist" in text_content


def test_recipient_inactive(client, users, db_session):
    sender, _, recipient = users

    recipient.is_active = False
    db_session.commit()

    response = client.post(
        "/command",
        data={
            "user_id": sender.username,
            "text": f"kudos {recipient.username} Hello"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["response_type"] == "ephemeral"
    text_content = get_text_from_block(data)
    assert "inactive" in text_content


def test_sender_inactive(client, users):
    _, inactive_sender, recipient = users

    response = client.post(
        "/command",
        data={
            "user_id": inactive_sender.username,
            "text": f"kudos {recipient.username} Hello"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["response_type"] == "ephemeral"
    text_content = get_text_from_block(data)
    assert "inactive" in text_content


def test_empty_message(client, users):
    sender, _, recipient = users

    response = client.post(
        "/command",
        data={
            "user_id": sender.username,
            "text": f"kudos {recipient.username}"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["response_type"] == "ephemeral"
    text_content = get_text_from_block(data)
    assert "Usage" in text_content


def test_missing_text(client, users):
    sender, _, _ = users
    response = client.post("/command", data={"user_id": sender.username})
    assert response.status_code == 400
    assert "Missing text" in response.json()["detail"]