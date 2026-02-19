from sqlalchemy import func
from fastapi import HTTPException
from database import SessionLocal
from models_db import KudosDB
from datetime import datetime, date

def get_leaderboard():
    db = SessionLocal()

    leaderboard = db.query(KudosDB.to_user, func.count(KudosDB.id).label("score"))\
        .group_by(KudosDB.to_user)\
        .order_by(func.count(KudosDB.id).desc())\
        .all()
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
    kudos = db.query(KudosDB).filter(KudosDB.to_user == username).all()
    if not kudos:
        db.close()
        raise HTTPException(status_code=404, detail="Kudos not found.")
    db.close()
    return kudos

def add_kudos(kudos):
    # give kodus
    if kudos.from_user == kudos.to_user:
        raise HTTPException( #error of http that tells the user we have an error
            status_code=400,
            detail="Sorry, you aren't allowed to give kudos to yourself. "
                   "Try giving kudos to one of your teammates instead!",
        )
    if check_too_many_kudos_in_day(kudos.from_user):
        raise HTTPException(
            status_code=400,
            detail="Sorry, you have already gave too many kudos today. "
                   "wait for tomorrow to continue!",
        )
    db = SessionLocal()
    db_kudos = KudosDB(
        from_user=kudos.from_user,
        to_user=kudos.to_user,
        message=kudos.message,
        time_created=datetime.now()
    )
    db.add(db_kudos)
    db.commit()
    db.refresh(db_kudos)
    db.close()
    return {
        "status": "received",
        "kudos_id": db_kudos.id
    }

#function that checks if the user has gave too many kudos in a day, with a default limit of 5
def check_too_many_kudos_in_day(user: str, k=5):
    db = SessionLocal()
    kudos = db.query(KudosDB).filter(KudosDB.from_user == user, func.date(KudosDB.time_created)==date.today()).all()
    db.close()
    if len(kudos) >= k:
        return True
    return False