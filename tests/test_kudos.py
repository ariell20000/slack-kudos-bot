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
def db_session():
    """Create a temporary in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def users(db_session):
    """Create sample users: Alice (active), Bob (active), Inactive (inactive)."""
    alice = User(username="alice", is_active=True, password_hash="hashed", role="user")
    bob = User(username="bob", is_active=True, password_hash="hashed", role="user")
    inactive_user = User(username="inactive", is_active=False, password_hash="hashed", role="user")

    db_session.add_all([alice, bob, inactive_user])
    db_session.commit()
    return alice, bob, inactive_user

# -------------------------------
# Kudos tests
# -------------------------------

def test_cannot_give_kudos_to_self(db_session, users):
    alice, _, _ = users
    kudos = Kudos(from_user="alice", to_user="alice", message="Self kudos")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos, alice, db_session)
    assert "You cannot give kudos to yourself" in str(excinfo.value)


def test_cannot_give_kudos_to_inactive(db_session, users):
    alice, _, inactive_user = users
    kudos = Kudos(from_user="alice", to_user="inactive", message="Hello inactive")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos, alice, db_session)
    assert "Inactive receiver" in str(excinfo.value)


def test_cannot_give_kudos_from_inactive(db_session, users):
    _, bob, inactive_user = users
    kudos = Kudos(from_user="inactive", to_user="bob", message="Hello from inactive")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos, inactive_user, db_session)
    assert "Inactive sender" in str(excinfo.value)


def test_limit_kudos_per_day(db_session, users):
    alice, bob, _ = users
    # Give 5 kudos to Bob
    for i in range(5):
        kudos = Kudos(from_user="alice", to_user="bob", message=f"Kudos {i}")
        add_kudos(kudos, alice, db_session)

    # Sixth kudos should fail
    kudos6 = Kudos(from_user="alice", to_user="bob", message="Kudos 6")
    with pytest.raises(Exception) as excinfo:
        add_kudos(kudos6, alice, db_session)
    assert "Too many kudos today" in str(excinfo.value)


def test_valid_kudos_is_added(db_session, users):
    alice, bob, _ = users
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


def test_leaderboard_counts_correctly(db_session, users):
    alice, bob, _ = users
    # Alice gives Bob 3 kudos
    for i in range(3):
        kudos = Kudos(from_user="alice", to_user="bob", message=f"Kudos {i}")
        add_kudos(kudos, alice, db_session)

    leaderboard = get_leaderboard(db_session)
    assert len(leaderboard) == 2  # Alice and Bob exist
    bob_entry = next(u for u in leaderboard if u["username"] == "bob")
    assert bob_entry["score"] == 3


def test_get_status_returns_correct_counts(db_session, users):
    alice, bob, _ = users
    # Alice gives Bob 2 kudos
    for i in range(2):
        kudos = Kudos(from_user="alice", to_user="bob", message=f"Kudos {i}")
        add_kudos(kudos, alice, db_session)

    status_alice = get_status("alice", db_session)
    status_bob = get_status("bob", db_session)

    assert status_alice["kudos_given"] == 2
    assert status_alice["kudos_received"] == 0
    assert status_alice["is_active"] is True

    assert status_bob["kudos_given"] == 0
    assert status_bob["kudos_received"] == 2
    assert status_bob["is_active"] is True