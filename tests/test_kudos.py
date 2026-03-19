import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models_db import Base, User, KudosDB
from models import Kudos
from services.services import add_kudos, get_leaderboard, get_status

# -------------------------------
# Fixtures
# -------------------------------


@pytest.fixture(scope="function")
def users(db_session):
    alice = User(username="alice", is_active=True, password_hash="hashed", role="user")
    bob = User(username="bob", is_active=True, password_hash="hashed", role="user")
    inactive_user = User(username="inactive_user", is_active=False, password_hash="hashed", role="user")  # פעיל

    db_session.add_all([alice, bob, inactive_user])
    db_session.commit()
    return alice, bob, inactive_user

@pytest.fixture
def active_users(db_session):
    alice = User(username="alice", is_active=True, password_hash="hashed", role="user")
    bob = User(username="bob", is_active=True, password_hash="hashed", role="user")
    charlie = User(username="charlie", is_active=True, password_hash="hashed", role="user")

    db_session.add_all([alice, bob, charlie])
    db_session.commit()

    return alice, bob, charlie

# -------------------------------
# Kudos logic tests
# -------------------------------

def test_cannot_give_kudos_to_self(db_session, active_users):
    alice, _, _ = active_users
    kudos = Kudos(from_user="alice", to_user="alice", message="Self kudos")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos, alice, db_session)
    assert "You cannot give kudos to yourself" in str(excinfo.value)


def test_cannot_give_kudos_to_inactive(db_session, users):
    alice, _, inactive_user = users
    kudos = Kudos(from_user="alice", to_user="inactive_user", message="Hello inactive")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos, alice, db_session)
    assert "Inactive receiver" in str(excinfo.value)


def test_cannot_give_kudos_from_inactive(db_session, users):
    _, bob, inactive_user = users
    kudos = Kudos(from_user="inactive", to_user="bob", message="Hello from inactive")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos, inactive_user, db_session)
    assert "Inactive sender" in str(excinfo.value)


def test_limit_kudos_per_day(db_session, active_users):
    alice, bob, _ = active_users
    # Give 5 kudos to Bob
    for i in range(5):
        kudos = Kudos(from_user="alice", to_user="bob", message=f"Kudos {i}")
        add_kudos(kudos, alice, db_session)

    # Sixth kudos should fail
    kudos6 = Kudos(from_user="alice", to_user="bob", message="Kudos 6")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos6, alice, db_session)
    assert "Too many kudos today" in str(excinfo.value)


def test_valid_kudos_is_added(db_session, active_users):
    alice, bob, _ = active_users
    kudos = Kudos(from_user="alice", to_user="bob", message="Great job!")
    result = add_kudos(kudos, alice, db_session)
    assert result["status"] == "received"
    assert result["kudos_id"] is not None

    # Verify stored in DB
    db_kudos = db_session.query(KudosDB).filter_by(id=result["kudos_id"]).first()
    assert db_kudos is not None
    assert db_kudos.message == "Great job!"
    assert db_kudos.from_user.username == "alice"
    assert db_kudos.to_user.username == "bob"


# -------------------------------
# leaderboard logic tests
# -------------------------------

def test_leaderboard_counts_correctly(db_session, active_users):
    alice, bob, charlie = active_users
    # Alice gives Bob 3 kudos
    for i in range(3):
        add_kudos(Kudos(from_user="alice", to_user="bob", message=f"Kudos {i}"), alice, db_session)

    leaderboard = get_leaderboard(db_session)
    assert len(leaderboard) == 3  # Alice, Bob, Charlie


def test_leaderboard_includes_users_without_kudos(db_session, active_users):
    alice, bob, charlie = active_users
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


def test_leaderboard_orders_correctly(db_session, active_users):
    alice, bob, charlie = active_users
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


def test_add_kudos_updates_leaderboard(db_session, active_users):
    alice, bob, charlie = active_users
    # Add Kudos
    add_kudos(Kudos(from_user="alice", to_user="charlie", message="Hi"), alice, db_session)
    leaderboard = get_leaderboard(db_session)
    scores = {entry["username"]: entry["score"] for entry in leaderboard}
    assert scores["charlie"] == 1
    assert scores["alice"] == 0


# -------------------------------
# status test
# -------------------------------


def test_get_status_returns_correct_info(db_session, active_users):
    alice, bob, charlie = active_users
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