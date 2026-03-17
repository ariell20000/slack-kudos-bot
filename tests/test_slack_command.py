# test_slack_command.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, HTTPException

from models_db import Base, User, KudosDB
from routers.slack import router as slack_router
from models import Kudos
from services.services import add_kudos
from core.dependencies import get_db


# ----------------------------
# Fixture: In-memory DB
# ----------------------------
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

# ----------------------------
# Fixture: FastAPI app with Slack router
# ----------------------------
@pytest.fixture
def app(db_session):
    app = FastAPI()
    app.include_router(slack_router)
    # Inject DB dependency
    app.dependency_overrides[get_db] = lambda: db_session
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

# ----------------------------
# Fixture: create users
# ----------------------------
@pytest.fixture
def users(db_session):
    active_sender = User(username="alice", password_hash="hashed", role="user", is_active=True)
    inactive_sender = User(username="bob", password_hash="hashed", role="user", is_active=False)
    recipient = User(username="charlie", password_hash="hashed", role="user", is_active=True)
    db_session.add_all([active_sender, inactive_sender, recipient])
    db_session.commit()
    return active_sender, inactive_sender, recipient

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
    assert "does not exist" in data["text"]

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
    assert "inactive" in data["text"]

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
    assert "inactive" in data["text"]

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
    assert "Usage" in data["text"]
    
def test_missing_text(client, users):
    sender, _, _ = users
    response = client.post("/command", data={"user_id": sender.username})
    assert response.status_code == 400
    assert "Missing text" in response.json()["detail"]