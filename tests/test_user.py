# tests/test_user.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from services.services import register_user
from models import UserCreate


from models_db import Base, User
from security import hash_password, verify_password


# ----------------------------
# Fixture: in-memory database session
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
# Tests
# ----------------------------
def test_password_hashing(db_session):
    user_data = UserCreate(
        username="secure_user",
        password="SuperSecret123"
    )

    register_user(user_data, db_session)

    db_user = db_session.query(User).filter_by(username="secure_user").first()

    assert db_user.password_hash != "SuperSecret123"
    assert verify_password("SuperSecret123", db_user.password_hash)


def test_unique_username_constraint(db_session):
    user_data = UserCreate(
        username="secure_user",
        password="SuperSecret123"
    )

    register_user(user_data, db_session)

    db_user = db_session.query(User).filter_by(username="secure_user").first()

    assert db_user.password_hash != "SuperSecret123"
    assert verify_password("SuperSecret123", db_user.password_hash)