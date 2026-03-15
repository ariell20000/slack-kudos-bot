# test_auth.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from models_db import Base, User
from services.services import register_user, login_user, delete_user, get_status
from security import verify_password


# ----------------------------
# DB fixture
# ----------------------------
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


# ----------------------------
# helper object for register/login
# ----------------------------
class UserInput:
    def __init__(self, username, password):
        self.username = username
        self.password = password


# ----------------------------
# register tests
# ----------------------------

def test_register_success(db_session):

    user = UserInput("alice", "1234")

    result = register_user(user, db_session)

    assert result["status"] == "created"

    db_user = db_session.query(User).filter_by(username="alice").first()

    assert db_user is not None


def test_password_is_hashed(db_session):

    user = UserInput("bob", "secret")

    register_user(user, db_session)

    db_user = db_session.query(User).filter_by(username="bob").first()

    assert db_user.password_hash != "secret"
    assert verify_password("secret", db_user.password_hash)


def test_empty_password_not_allowed(db_session):

    user = UserInput("charlie", "")

    with pytest.raises(ValueError):
        register_user(user, db_session)


def test_unique_username(db_session):

    u1 = UserInput("same", "1")
    u2 = UserInput("same", "2")

    register_user(u1, db_session)

    with pytest.raises(IntegrityError):
        register_user(u2, db_session)


# ----------------------------
# login tests
# ----------------------------

def test_login_success(db_session):

    user = UserInput("login_user", "123")

    register_user(user, db_session)

    token = login_user(user, db_session)

    assert "access_token" in token


def test_login_wrong_password(db_session):

    register_user(UserInput("bob", "123"), db_session)

    wrong = UserInput("bob", "wrong")

    with pytest.raises(Exception):
        login_user(wrong, db_session)


def test_login_user_not_found(db_session):

    user = UserInput("ghost", "123")

    with pytest.raises(Exception):
        login_user(user, db_session)


# ----------------------------
# inactive user tests
# ----------------------------

def test_inactive_user_cannot_login(db_session):

    user = UserInput("inactive", "123")

    register_user(user, db_session)

    db_user = db_session.query(User).filter_by(username="inactive").first()

    db_user.is_active = False
    db_session.commit()

    with pytest.raises(Exception):
        login_user(user, db_session)


# ----------------------------
# delete user (soft delete)
# ----------------------------

def test_delete_user_sets_inactive(db_session):

    user = UserInput("to_delete", "123")

    register_user(user, db_session)

    delete_user("to_delete", db_session)

    db_user = db_session.query(User).filter_by(username="to_delete").first()

    assert db_user.is_active is False


# ----------------------------
# status tests
# ----------------------------

def test_status_for_new_user(db_session):

    user = UserInput("status_user", "123")

    register_user(user, db_session)

    status = get_status("status_user", db_session)

    assert status["kudos_given"] == 0
    assert status["kudos_received"] == 0
    assert status["is_active"] is True


def test_status_user_not_found(db_session):

    with pytest.raises(Exception):
        get_status("ghost", db_session)


# ----------------------------
# role test
# ----------------------------

def test_default_role_is_user(db_session):

    user = UserInput("role_user", "123")

    register_user(user, db_session)

    db_user = db_session.query(User).filter_by(username="role_user").first()

    assert db_user.role == "user"