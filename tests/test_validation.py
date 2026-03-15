import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models_db import Base, User
from services.services import register_user, add_kudos
from models import Kudos, UserCreate
from security import hash_password


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


# ============================
# register validation
# ============================

def test_username_empty(db_session):

    user = UserCreate(
        username="",
        password="1234"
    )

    with pytest.raises(ValueError):
        register_user(user, db_session)


def test_username_too_short(db_session):

    user = UserCreate(
        username="ab",
        password="1234"
    )

    with pytest.raises(ValueError):
        register_user(user, db_session)


def test_password_empty(db_session):

    user = UserCreate(
        username="alice",
        password=""
    )

    with pytest.raises(ValueError):
        register_user(user, db_session)


def test_password_too_short(db_session):

    user = UserCreate(
        username="alice",
        password="1"
    )

    with pytest.raises(ValueError):
        register_user(user, db_session)


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