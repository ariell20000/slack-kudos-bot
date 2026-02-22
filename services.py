from sqlalchemy import func
from fastapi import HTTPException
from database import SessionLocal
from models_db import KudosDB, User
from datetime import datetime, date

def get_leaderboard():
    db = SessionLocal()
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

    db.close()
    return [{"username": user, "score": score} for user, score in leaderboard]

def get_kudos_by_id(kudos_id: int):
    db = SessionLocal()
    kudos = db.get(KudosDB, kudos_id)
    if not kudos:
        db.close()
        raise HTTPException(status_code=404, detail="Kudos not found.")
    db.close()
    return kudos

def delete_kudos_by_id(kudos_id: int):
    db = SessionLocal()
    kudos = db.get(KudosDB, kudos_id)

    if not kudos:
        db.close()
        raise HTTPException(status_code=404, detail="Kudos not found.")
    db.delete(kudos)
    db.commit()
    db.close()
    return {"status": "deleted"}

def get_kudoses_by_username(username: str):
    db = SessionLocal()
    if not check_user_exists(db, username):
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")
    user = db.query(User).filter(User.username == username).first()
    kudoses = db.query(KudosDB).filter(KudosDB.to_user_id == user.id).all()
    db.close()
    return kudoses

def add_kudos(kudos):
    # give kodus
    if kudos.from_user == kudos.to_user:
        raise HTTPException( #error of http that tells the user we have an error
            status_code=400,
            detail="Sorry, you aren't allowed to give kudos to yourself. "
                   "Try giving kudos to one of your teammates instead!",
        )
    db = SessionLocal()
    try:
        if not check_user_active(db, kudos.from_user):
            raise HTTPException(
                status_code=400,
                detail="Sorry, you aren't allowed to give kudos from an inactive user.",
            )
        if not check_user_active(db, kudos.to_user):
            raise HTTPException(
                status_code=400,
                detail="Sorry, you aren't allowed to give kudos to an inactive user. "
                       "Try giving kudos to one of your active teammates instead!",
            )
        if not check_user_exists(db, kudos.from_user):
            create_user(db, kudos.from_user)
        if not check_user_exists(db, kudos.to_user):
            create_user(db, kudos.to_user)
        query1= db.query(User).filter(User.username  == kudos.from_user).first()
        query2= db.query(User).filter(User.username  == kudos.to_user).first()
        id1=query1.id
        id2=query2.id
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
        db.commit()
        db.refresh(db_kudos)
    finally:
        db.close()
    return {
        "status": "received",
        "kudos_id": db_kudos.id
    }

def get_status(username: str):
    db=SessionLocal()
    user=db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")
    kodus_given= db.query(KudosDB).filter(KudosDB.from_user_id == user.id).count()
    kudos_received= db.query(KudosDB).filter(KudosDB.to_user_id == user.id).count()
    db.close()
    return {
        "username": username,
        "kudos_given": kodus_given,
        "kudos_received": kudos_received,
        "is_active": user.is_active
    }

def add_user(username: str):
    db = SessionLocal()
    try:
        return create_user(db, username)
    finally:
        db.close()

def delete_user(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    db.commit()
    db.close()
    return {"status": "deleted"}

#function that checks if the user has gave too many kudos in a day, with a default limit of 5
def check_too_many_kudos_in_day(db, user_id, k=5):
    kudosnum = db.query(KudosDB).filter(KudosDB.from_user_id == user_id, func.date(KudosDB.time_created)==date.today()).count()
    if kudosnum >= k:
        return True
    return False

def create_user(db, username: str):
    if check_user_exists(db, username):
        raise HTTPException(status_code=400, detail="Username already exists.")
    new_user = User(username=username)
    db.add(new_user)
    return {"status": "created", "username": new_user.username}

def check_user_exists(db, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    return True

def check_user_active(db, username: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not user.is_active:
        return False
    return True