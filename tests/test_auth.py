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
from security import verify_password, decode_access_token
from models import UserCreate



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
# register tests
# ----------------------------

def test_register_success(db_session):

    user = UserCreate(username="alice", password="1234")

    result = register_user(user, db_session)

    assert result["status"] == "created"

    db_user = db_session.query(User).filter_by(username="alice").first()

    assert db_user is not None


def test_password_is_hashed(db_session):

    user = UserCreate(username="bob", password="secret")

    register_user(user, db_session)

    db_user = db_session.query(User).filter_by(username="bob").first()

    assert db_user.password_hash != "secret"
    assert verify_password("secret", db_user.password_hash)


# ----------------------------
# login tests
# ----------------------------

def test_login_success(db_session):

    user = UserCreate(username="login_user", password="1234")

    register_user(user, db_session)

    token = login_user(user, db_session)

    assert "access_token" in token


def test_login_wrong_password(db_session):

    register_user(UserCreate(username="bob", password="1234"), db_session)

    wrong = UserCreate(username="bob",password= "wrong")

    with pytest.raises(Exception):
        login_user(wrong, db_session)


def test_login_user_not_found(db_session):

    user = UserCreate(username="ghost", password="1234")

    with pytest.raises(Exception):
        login_user(user, db_session)


# ----------------------------
# inactive user tests
# ----------------------------

def test_inactive_user_cannot_login(db_session):

    user = UserCreate(username="inactive",password= "1234")

    register_user(user, db_session)

    db_user = db_session.query(User).filter_by(username="inactive").first()

    db_user.is_active = False
    db_session.commit()

    with pytest.raises(Exception):
        login_user(user, db_session)

# ----------------------------
# status tests
# ----------------------------

def test_status_for_new_user(db_session):

    user = UserCreate(username="status_user", password="1234")

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

    user = UserCreate(username="role_user",password= "1234")

    register_user(user, db_session)

    db_user = db_session.query(User).filter_by(username="role_user").first()

    assert db_user.role == "user"

def test_jwt_contains_correct_sub(db_session):
    user = UserCreate(username="jwt_user", password="supersecret")
    register_user(user, db_session)

    token_data = login_user(user, db_session)
    token = token_data["access_token"]

    payload = decode_access_token(token)

    assert payload["sub"] == "jwt_user"