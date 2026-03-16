# models.py

from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, AfterValidator

def is_empty(s: str):
    if s.strip() == "":
        raise ValueError("Field cannot be empty")
    return s

def too_short(min_length: int):
    def validator(s: str):
        if len(s) < min_length:
            raise ValueError(
                f"Field must be at least {min_length} characters long"
            )
        return s
    return validator
def contains_no_spaces(s: str):
    if " " in s:
        raise ValueError("Field cannot contain spaces")
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
    username: Annotated[str,AfterValidator(is_empty),AfterValidator(contains_no_spaces), AfterValidator(too_short(2))]
    password: Annotated[str,AfterValidator(is_empty),AfterValidator(contains_no_spaces), AfterValidator(too_short(4))]

# data model for user login
class UserLogin(BaseModel):
    username: str
    password: str
