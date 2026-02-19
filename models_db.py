from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class KudosDB(Base):
    __tablename__ = "kudos"

    id = Column(Integer, primary_key=True, index=True)
    from_user = Column(String, nullable=False)
    to_user = Column(String, nullable=False)
    message = Column(String, nullable=False)
    time_created = Column(DateTime, nullable=False)
