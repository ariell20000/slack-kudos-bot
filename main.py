from fastapi import FastAPI, HTTPException

from database import engine
from models_db import Base

import services
from models import Kudos
import storage
import models_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

storage.scores
storage.log
storage.user_log

#main domain
@app.get("/")
def home():
    return {"message": "Server is alive"}

#subdomain that check if sever is alive
@app.get("/ping")
def ping():
    return {"status": "ok"}

#subdomain that returns leaderboard
@app.get("/leaderboard")
def get_leaderboard():
    return services.get_leaderboard()


#subdomain that returns kudos by id
@app.get("/kudos/{kudos_id}")
def get_kudos_by_id(kudos_id: int):
    return services.get_kudos_by_id(kudos_id)

#subdomain that deletes kudos by id
@app.delete("/kudos/{kudos_id}")
def delete_kudos_by_id(kudos_id: int):
    return services.delete_kudos_by_id(kudos_id)

#subdomain that returns kudos by username
@app.get("/user/{username}")
def get_kudoses_by_username(username: str):
    return services.get_kudoses_by_username(username)

@app.post("/kudos")
def add_kudos(kudos: Kudos):
    return services.add_kudos(kudos)

