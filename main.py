from fastapi import FastAPI

from database import engine
from models_db import Base

import services
from models import Kudos, UserFullResponse, KudosResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

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
@app.get("/kudos/{kudos_id}", response_model=KudosResponse)
def get_kudos_by_id(kudos_id: int):
    return services.get_kudos_by_id(kudos_id)

#subdomain that deletes kudos by id
@app.delete("/kudos/{kudos_id}")
def delete_kudos_by_id(kudos_id: int):
    return services.delete_kudos_by_id(kudos_id)

#subdomain that returns kudos by username
@app.get("/user/{username}", response_model=list[KudosResponse])
def get_kudos_by_username(username: str):
    return services.get_kudos_by_username(username)

@app.post("/kudos")
def add_kudos(kudos: Kudos):
    return services.add_kudos(kudos)

@app.get("/user/{username}/stats")
def get_status(username: str):
    return services.get_status(username)

@app.post("/create/user/{username}")
def add_user(username: str):
    return services.add_user(username)

@app.delete("/user/{username}")
def delete_user(username: str):
    return services.delete_user(username)

@app.get("/users/data", response_model=list[UserFullResponse])
def get_users_data():
    return services.get_users_data()