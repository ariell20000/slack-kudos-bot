#tests/test_validation.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pydantic import ValidationError


from models_db import User
from services.auth_service import register_user
from services.kudos_service import add_kudos
from models import Kudos, UserCreate
from security import hash_password, verify_password


# ----------------------------
# Tests
# ----------------------------


# ============================
# register validation
# ============================

def test_username_empty():

    with pytest.raises(ValidationError):
        UserCreate(
            username="",
            password="1234"
        )


def test_username_too_short():

    with pytest.raises(ValidationError):
        UserCreate(
            username="a",
            password="1234"
        )

def test_password_empty():

    with pytest.raises(ValidationError):
        UserCreate(
            username="alice",
            password=""
        )

def test_password_too_short():

    with pytest.raises(ValidationError):
        UserCreate(
            username="alice",
            password="1"
        )

# ============================
# kudos validation
# ============================

def test_kudos_empty_message(db_session):

    alice = User(
        username="alice",
        password_hash=hash_password("1234")
    )

    bob = User(
        username="bob",
        password_hash=hash_password("1234")
    )

    db_session.add_all([alice, bob])
    db_session.commit()

    with pytest.raises(Exception) as excinfo:
        Kudos(
            from_user="alice",
            to_user="bob",
            message=""
        )
    assert "Field cannot be empty" in str(excinfo.value)


def test_kudos_message_too_long(db_session):

    alice = User(
        username="alice",
        password_hash=hash_password("1234")
    )

    bob = User(
        username="bob",
        password_hash=hash_password("1234")
    )

    db_session.add_all([alice, bob])
    db_session.commit()

    msg = "a" * 500

    kudos = Kudos(
        from_user="alice",
        to_user="bob",
        message=msg
    )

    with pytest.raises(Exception):
        add_kudos(kudos, alice, db_session)

def test_unique_username_constraint(db_session):
    user_data = UserCreate(
        username="secure_user",
        password="SuperSecret123"
    )

    register_user(user_data, db_session)

    db_user = db_session.query(User).filter_by(username="secure_user").first()

    assert db_user.password_hash != "SuperSecret123"
    assert verify_password("SuperSecret123", db_user.password_hash)