from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from database import SessionLocal
from models_db import KudosDB, User
from datetime import datetime, date
from models import KudosResponse, UserFullResponse

def get_leaderboard(db: SessionLocal):
    leaderboard = (db.query(
        User.username,
        func.count(KudosDB.id).label("score")
    ).join(
        KudosDB, User.id == KudosDB.to_user_id
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

def add_kudos(kudos, db: SessionLocal):
    # give kodus
    if kudos.from_user == kudos.to_user:
        raise HTTPException( #error of http that tells the user we have an error
            status_code=400,
            detail="Sorry, you aren't allowed to give kudos to yourself. "
                   "Try giving kudos to one of your teammates instead!",
        )
    with db.begin():
        from_user = db.query(User).filter(User.username == kudos.from_user).with_for_update().first()
        to_user = db.query(User).filter(User.username == kudos.to_user).first()
        if not from_user:
            from_user = User(username=kudos.from_user)
            db.add(from_user)
            db.flush()  # Ensure from_user.id is populated before using it
        if not to_user:
            to_user = User(username=kudos.to_user)
            db.add(to_user)
            db.flush()  # Ensure to_user.id is populated before using it
        if not from_user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Sorry, you aren't allowed to give kudos from an inactive user.",
            )
        if not to_user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Sorry, you aren't allowed to give kudos to an inactive user. "
                       "Try giving kudos to one of your active teammates instead!",
            )
        id1=from_user.id
        id2=to_user.id
        if check_too_many_kudos_in_day(db, id1):
            raise HTTPException(
                status_code=400,
                detail="Sorry, you have already gave too many kudos today. "
                       "wait for tomorrow to continue!",
            )
        db_kudos = KudosDB(
            from_user_id=id1,
            to_user_id=id2,
            message=kudos.message,
            time_created=datetime.now()
        )
        db.add(db_kudos)
        db.flush()  # Ensure db_kudos.id is populated before returning it
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

def add_user(username: str, db: SessionLocal):
    with db.begin():
        user = db.query(User).filter(User.username == username).first()
        if user:
            raise HTTPException(status_code=404, detail="User already exists..")
    return create_user(db, username)

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
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")

# def check_user_exists(db: SessionLocal, username: str):
#     user = db.query(User).filter(User.username == username).first()
#     if not user:
#         return False
#     return True

# def check_user_active(db: SessionLocal, username: str):
#     user = db.query(User).filter(User.username == username).first()
#     if not user:
#         return False
#     if not user.is_active:
#         return False
#     return True