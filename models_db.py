from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from database import Base
from sqlalchemy.orm import relationship


class KudosDB(Base):
    __tablename__ = "kudos"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)
    time_created = Column(DateTime, nullable=False)
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="given_kudos")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_kudos")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    received_kudos = relationship("KudosDB", foreign_keys=[KudosDB.to_user_id], back_populates="to_user")
    given_kudos = relationship("KudosDB", foreign_keys=[KudosDB.from_user_id], back_populates="from_user")



