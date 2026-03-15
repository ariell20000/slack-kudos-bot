# tests/test_leaderboard.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_db import Base, User
from services.services import add_kudos, get_leaderboard, get_status
from models import Kudos
from security import hash_password

# single in-memory engine shared across all tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # create all tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    # drop tables after test to start fresh
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def users(db_session):
    # create test users with dummy passwords
    alice = User(username="alice", password_hash=hash_password("dummy1"))
    bob = User(username="bob", password_hash=hash_password("dummy2"))
    charlie = User(username="charlie", password_hash=hash_password("dummy3"))
    db_session.add_all([alice, bob, charlie])
    db_session.commit()
    return alice, bob, charlie

def test_leaderboard_includes_users_without_kudos(db_session, users):
    alice, bob, charlie = users
    # Initially no kudos
    leaderboard = get_leaderboard(db_session)
    usernames = [entry["username"] for entry in leaderboard]
    # All users should appear, even if score is 0
    assert "alice" in usernames
    assert "bob" in usernames
    assert "charlie" in usernames
    scores = {entry["username"]: entry["score"] for entry in leaderboard}
    for score in scores.values():
        assert score == 0


def test_leaderboard_orders_correctly(db_session, users):
    alice, bob, charlie = users
    # Alice gives 2 kudos to Bob, 1 to Charlie
    add_kudos(Kudos(from_user="alice", to_user="bob", message="K1"), alice, db_session)
    add_kudos(Kudos(from_user="alice", to_user="bob", message="K2"), alice, db_session)
    add_kudos(Kudos(from_user="alice", to_user="charlie", message="K3"), alice, db_session)

    leaderboard = get_leaderboard(db_session)
    # Bob should be first (2 kudos), Charlie second (1), Alice last (0)
    assert leaderboard[0]["username"] == "bob"
    assert leaderboard[0]["score"] == 2
    assert leaderboard[1]["username"] == "charlie"
    assert leaderboard[1]["score"] == 1
    assert leaderboard[-1]["username"] == "alice"
    assert leaderboard[-1]["score"] == 0


def test_add_kudos_updates_leaderboard(db_session, users):
    alice, bob, charlie = users
    # Add Kudos
    add_kudos(Kudos(from_user="alice", to_user="charlie", message="Hi"), alice, db_session)
    leaderboard = get_leaderboard(db_session)
    scores = {entry["username"]: entry["score"] for entry in leaderboard}
    assert scores["charlie"] == 1
    assert scores["alice"] == 0


def test_get_status_returns_correct_info(db_session, users):
    alice, bob, charlie = users
    # Alice gives Bob 1 kudos
    add_kudos(Kudos(from_user="alice", to_user="bob", message="Nice"), alice, db_session)
    status_alice = get_status("alice", db_session)
    status_bob = get_status("bob", db_session)

    assert status_alice["kudos_given"] == 1
    assert status_alice["kudos_received"] == 0
    assert status_bob["kudos_given"] == 0
    assert status_bob["kudos_received"] == 1
    assert status_alice["is_active"] is True
    assert status_bob["is_active"] is True