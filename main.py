from fastapi import FastAPI
from database import engine
from models_db import Base

from routers import auth, kudos, users

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(kudos.router)
app.include_router(users.router)
