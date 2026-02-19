from sqlalchemy import func
from fastapi import HTTPException
from database import SessionLocal
from models_db import KudosDB
from datetime import datetime, date
import storage

def get_leaderboard():
    leaderboard = sorted(storage.scores.items(), key=lambda item: item[1], reverse=True)
    newleaderboard = []
    for name, score in leaderboard:
        newleaderboard.append({"user": name, "score": score})
    return newleaderboard

def get_kudos_by_id(kudos_id: int):
    if (kudos_id not in KudosDB):
        raise HTTPException(
            status_code=404,
            detail="Kudos not found. Please check the kudos ID and try again.",
        )
    return storage.log[kudos_id]

def delete_kudos_by_id(kudos_id: int):
    if (kudos_id not in storage.log):
        raise HTTPException(
            status_code=404,
            detail="Kudos not found. Please check the kudos ID and try again.",
        )
    kudos = storage.log[kudos_id]
    # Update score for the receiver
    if storage.scores[kudos.to_user]==1:
        del storage.scores[kudos.to_user]
    else:
        storage.scores[kudos.to_user] = storage.scores[kudos.to_user] - 1
    # update logs
    del storage.log[kudos_id]
    if len(storage.user_log[kudos.to_user]) == 1:
        del storage.user_log[kudos.to_user]
    else:
        storage.user_log[kudos.to_user].remove(kudos)
    return {"status": "deleted", "kudos_id": kudos_id}

def get_kudoses_by_username(username: str):
    if (username not in storage.user_log):
        return []
    return storage.user_log[username]

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