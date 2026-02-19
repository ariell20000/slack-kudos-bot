from datetime import datetime
from fastapi import HTTPException

from models import Kudos
import storage

def get_leaderboard():
    leaderboard = sorted(storage.scores.items(), key=lambda item: item[1], reverse=True)
    newleaderboard = []
    for name, score in leaderboard:
        newleaderboard.append({"user": name, "score": score})
    return newleaderboard

def get_kudos_by_id(kudos_id: int):
    if (kudos_id not in storage.log):
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

def add_kudos(kudos: Kudos):
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
    kudos.kudos_id = storage.kudos_id_counter
    storage.kudos_id_counter+=1
    kudos.time_created = datetime.now()
    # Update score for the receiver
    storage.scores[kudos.to_user] = storage.scores.get(kudos.to_user, 0) + 1
    # update logs
    storage.log[kudos.kudos_id]=kudos
    storage.user_log.setdefault(kudos.to_user, []).append(kudos)
    #echo back the kudos data
    return {
        "status": "received",
        "from": kudos.from_user,
        "to": kudos.to_user,
        "message": kudos.message,
        "kudos_id": kudos.kudos_id
    }


#function that checks if the user has gave too many kudos in a day, with a default limit of 5
def check_too_many_kudos_in_day(user: str, k=5):
    today = datetime.now().date()
    count = 0
    for id in storage.log:
        if storage.log[id].from_user == user and storage.log[id].time_created.date() == today:
            count += 1
    return count >= k