from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models_db import Base

import services
from models import Kudos, UserFullResponse, KudosResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
def get_leaderboard(db: Session = Depends(get_db)):
    return services.get_leaderboard(db)


#subdomain that returns kudos by id
@app.get("/kudos/{kudos_id}", response_model=KudosResponse)
def get_kudos_by_id(kudos_id: int, db: Session = Depends(get_db)):
    return services.get_kudos_by_id(kudos_id, db)

#subdomain that deletes kudos by id
@app.delete("/kudos/{kudos_id}")
def delete_kudos_by_id(kudos_id: int, db: Session = Depends(get_db)):
    return services.delete_kudos_by_id(kudos_id, db)

#subdomain that returns kudos by username
@app.get("/user/{username}", response_model=list[KudosResponse])
def get_kudos_by_username(username: str, db: Session = Depends(get_db)):
    return services.get_kudos_by_username(username, db)

@app.post("/kudos")
def add_kudos(kudos: Kudos, db: Session = Depends(get_db)):
    return services.add_kudos(kudos, db)

@app.get("/user/{username}/stats")
def get_status(username: str, db: Session = Depends(get_db)):
    return services.get_status(username, db)

@app.post("/create/user/{username}")
def add_user(username: str, db: Session = Depends(get_db)):
    return services.add_user(username, db)

@app.delete("/user/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    return services.delete_user(username, db)

@app.get("/users/data", response_model=list[UserFullResponse])
def get_users_data(db: Session = Depends(get_db)):
    return services.get_users_data(db)