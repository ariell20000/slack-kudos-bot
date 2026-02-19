from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base

class KudosDB(Base):
    __tablename__ = "kudos"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)
    time_created = Column(DateTime, nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

