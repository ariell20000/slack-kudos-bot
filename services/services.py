# services.py

from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from database import SessionLocal
from models_db import KudosDB, User
from datetime import datetime, date
from models import KudosResponse, UserFullResponse
from security import hash_password
from security import verify_password, create_access_token


def get_leaderboard(db: SessionLocal):
    leaderboard = (db.query(
        User.username,
        func.count(KudosDB.id).label("score")
    ).outerjoin(KudosDB, User.id == KudosDB.to_user_id # LEFT OUTER JOIN, TO INCLUDE USERS WITH 0 KUDOS
    ).filter(User.is_active==True).
        group_by(
        User.id, User.username
    ).order_by(
        func.count(KudosDB.id).desc()    ).
                   all())

    return [{"username": user, "score": score} for user, score in leaderboard]

def get_kudos_by_id(kudos_id: int, db: SessionLocal):
    kudos = db.get(KudosDB, kudos_id)
    if not kudos:
        raise HTTPException(status_code=404, detail="Kudos not found.")
    kudos_res= KudosResponse(
        message=kudos.message,
        from_user=kudos.from_user.username,
        time_created=kudos.time_created
    )
    return kudos_res

def delete_kudos_by_id(kudos_id: int, db: SessionLocal):
    with db.begin():
        kudos = db.get(KudosDB, kudos_id)
        if not kudos:
            raise HTTPException(status_code=404, detail="Kudos not found.")
        db.delete(kudos)
    return {"status": "deleted"}

def get_kudos_by_username(username: str, db: SessionLocal):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    kudos = user.received_kudos
    kudos_res = []
    for k in kudos:
        kudos_res.append(KudosResponse(
            message=k.message,
            from_user=k.from_user.username,
            time_created=k.time_created
        ))
    return kudos_res

def add_kudos(kudos, current_user, db: SessionLocal):
    if not kudos.to_user:
        raise HTTPException(400, "Missing receiver")

    if not kudos.message:
        raise HTTPException(400, "Message cannot be empty")

    if len(kudos.message) > 200:
        raise HTTPException(400, "Message too long")

    if kudos.from_user == kudos.to_user:
        raise HTTPException(
            status_code=400,
            detail="You cannot give kudos to yourself"
        )

    from_user = current_user
    to_user = db.query(User).filter(
        User.username == kudos.to_user
    ).first()

    if not from_user:
        raise HTTPException(404, "From user not found")

    if not to_user:
        raise HTTPException(404, "To user not found")

    if not from_user.is_active:
        raise HTTPException(400, "Inactive sender")

    if not to_user.is_active:
        raise HTTPException(400, "Inactive receiver")

    id1 = from_user.id
    id2 = to_user.id

    if check_too_many_kudos_in_day(db, id1):
        raise HTTPException(400, "Too many kudos today")

    db_kudos = KudosDB(
        from_user_id=id1,
        to_user_id=id2,
        message=kudos.message,
        time_created=datetime.now()
    )

    db.add(db_kudos)

    db.commit()

    db.refresh(db_kudos)

    return {
        "status": "received",
        "kudos_id": db_kudos.id
    }
def get_status(username: str, db: SessionLocal):
    user=db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    kodus_given= db.query(KudosDB).filter(KudosDB.from_user_id == user.id).count()
    kudos_received= db.query(KudosDB).filter(KudosDB.to_user_id == user.id).count()
    return {
        "username": username,
        "kudos_given": kodus_given,
        "kudos_received": kudos_received,
        "is_active": user.is_active
    }

def register_user(user_data, db):
    if not user_data.username:
        raise ValueError("Username cannot be empty")
    if len(user_data.username) < 3:
        raise ValueError("Username too short")
    if not user_data.password:
        raise ValueError("Password cannot be empty")
    if len(user_data.password) < 4:
        raise ValueError("Password too short")

    with db.begin():
        hashed = hash_password(user_data.password)
        new_user = User(
            username=user_data.username,
            password_hash=hashed
        )
        db.add(new_user)
    return {"status": "created"}

def login_user(user_data, db):
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def delete_user(username: str, db: SessionLocal):
    with db.begin():
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        user.is_active = False
    return {"status": "deleted"}

def get_users_data(db: SessionLocal):
    users = (
        db.query(User)
        .options(
            joinedload(User.received_kudos)
            .joinedload(KudosDB.from_user)
        )
        .all()
    )

    users_data = []

    for user in users:
        kudos_res=[]
        for k in user.received_kudos:
            kudos_res.append(KudosResponse(
                message=k.message,
                from_user=k.from_user.username,
                time_created=k.time_created
            ))
        users_data.append(UserFullResponse(
            username=user.username,
            is_active=user.is_active,
            kudos_received=kudos_res
         )

    )
    return users_data



#function that checks if the user has gave too many kudos in a day, with a default limit of 5
def check_too_many_kudos_in_day(db: SessionLocal, user_id, k=5):
    kudosnum = db.query(KudosDB).filter(KudosDB.from_user_id == user_id, func.date(KudosDB.time_created)==date.today()).count()
    if kudosnum >= k:
        return True
    return False

def create_user(db, username):
    try:
        new_user = User(username=username)
        db.add(new_user)
        db.commit()
        return {"status": "created"}
    except IntegrityError:
        # Rollback the transaction to clear the failed insert
        # relevant in race conditions where two requests try to create the same user at the same time
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

