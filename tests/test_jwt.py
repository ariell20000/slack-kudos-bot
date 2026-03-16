# tests/test_jwt.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import jwt
from fastapi import HTTPException
from models_db import User
from services.services import login_user, register_user
from security import verify_password, create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_db import Base
from security import hash_password


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(db_session):
    user = User(username="alice", password_hash=hash_password("1234"))
    db_session.add(user)
    db_session.commit()
    return user


# ----------------------------
# Test login and token creation
# ----------------------------
def test_login_creates_jwt(db_session, test_user):
    token_data = login_user(type("UserData", (), {"username": "alice", "password": "1234"})(), db_session)
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_wrong_password_raises(db_session, test_user):
    with pytest.raises(HTTPException) as excinfo:
        login_user(type("UserData", (), {"username": "alice", "password": "wrong"})(), db_session)
    assert excinfo.value.status_code == 401


def test_login_nonexistent_user_raises(db_session):
    with pytest.raises(HTTPException) as excinfo:
        login_user(type("UserData", (), {"username": "ghost", "password": "1234"})(), db_session)
    assert excinfo.value.status_code == 401


def test_token_contains_correct_sub(test_user):
    token = create_access_token({"sub": test_user.username})
    payload = jwt.decode(token, options={"verify_signature": False})
    assert payload["sub"] == "alice"