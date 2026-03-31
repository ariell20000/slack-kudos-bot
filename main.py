#main.py

from fastapi import FastAPI
from database import engine
from models_db import Base

from routers import auth, kudos, users, slack

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kudos Slack Bot API",
    description="A Slack bot for sending kudos with JWT authentication and role-based access control.",
    version="1.0.0",
)

app.include_router(slack.router, prefix="/slack", tags=["Slack"])
app.include_router(auth.router)
app.include_router(kudos.router)
app.include_router(users.router)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {"status": "healthy"}
