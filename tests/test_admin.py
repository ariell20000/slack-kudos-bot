#tests/test_admin.py

import sys
import os



sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi import HTTPException


from models_db import User
from services.services import delete_user, get_users_data, delete_kudos_by_id, add_kudos
from security import hash_password
from models import Kudos


# -------------------------------
# fixtures
# -------------------------------

@pytest.fixture
def users(db_session):

    admin = User(
        username="admin",
        password_hash=hash_password("1234"),
        role="admin"
    )

    alice = User(
        username="alice",
        password_hash=hash_password("1234"),
        role="user"
    )

    bob = User(
        username="bob",
        password_hash=hash_password("1234"),
        role="user"
    )

    db_session.add_all([admin, alice, bob])
    db_session.commit()

    return admin, alice, bob


def test_only_admin_can_delete_kodus(db_session, users):

    admin, alice, bob = users
    kudos = Kudos(from_user="alice", to_user="bob", message="example")
    with pytest.raises(HTTPException):
        delete_kudos_by_id(kudos.kudos_id, alice, db_session)

def test_admin_can_delete_kudos(db_session, users):

    admin, alice, bob = users

    kudos = Kudos(from_user="alice", to_user="bob", message="hi")

    result = add_kudos(kudos, alice, db_session)

    delete_kudos_by_id(result["kudos_id"], admin, db_session)



def test_delete_kudos_not_found(db_session, users):

    admin, _, _ = users

    with pytest.raises(HTTPException):
        delete_kudos_by_id(999, admin, db_session)



def test_admin_can_delete_user(db_session, users):

    admin, _, bob = users

    delete_user("bob", admin, db_session)

    user = db_session.query(User).filter_by(username="bob").first()

    assert user.is_active is False


def test_user_cant_delete_user(db_session, users):
    admin, alice, bob = users

    with pytest.raises(HTTPException):
        delete_user("bob", alice, db_session)

def test_delete_user_not_found(db_session, users):

    admin, _, _ = users

    with pytest.raises(HTTPException):
        delete_user("ghost", admin, db_session)


def test_get_users_data_returns_list(db_session, users):

    admin, _, _ = users

    data = get_users_data(admin, db_session)

    assert len(data) >= 1

def test_only_admin_can_get_users(db_session, users):

    admin, alice, _ = users

    get_users_data(admin, db_session)

    with pytest.raises(HTTPException):
        get_users_data(alice, db_session)


