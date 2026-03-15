# models.py

from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, AfterValidator

#function to check if the string is empty or not
def is_empty(s: str):
    if s.strip() == "":
        raise ValueError("Field cannot be empty")
    return s

# data model for kudos
class Kudos(BaseModel):
    from_user: Annotated[str, AfterValidator(is_empty)]
    to_user: Annotated[str, AfterValidator(is_empty)]
    message: Annotated[str, AfterValidator(is_empty)]
    kudos_id: Optional[int] = None
    time_created: Optional[datetime] = None

# response model for kudos
class KudosResponse(BaseModel):
    message: str
    from_user: str
    time_created: datetime

# response model for user data
class UserFullResponse(BaseModel):
    username: str
    is_active: bool
    kudos_received: list[KudosResponse]

# data model for user creation
class UserCreate(BaseModel):
    username: str
    password: str

# data model for user login
class UserLogin(BaseModel):
    username: str
    password: str
