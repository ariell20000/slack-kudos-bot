#models.py

from typing import Optional, Annotated, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, AfterValidator, Field


def is_empty(s: str):
    """Validator that ensures a string is not empty or just whitespace.

    Args:
        s (str): The string to validate.

    Returns:
        str: The original string if valid.

    Raises:
        ValueError: If the string is empty or only whitespace.
    """
    if s.strip() == "":
        raise ValueError("Field cannot be empty")
    return s

def too_short(min_length: int):
    """Factory that returns a validator ensuring a string meets a minimum length.

    Args:
        min_length (int): Minimum allowed length for the string.

    Returns:
        Callable[[str], str]: A validator function that raises ValueError if too short.
    """
    def validator(s: str):
        if len(s) < min_length:
            raise ValueError(
                f"Field must be at least {min_length} characters long"
            )
        return s
    return validator
def contains_no_spaces(s: str):
    """Validator that ensures a string contains no space characters.

    Args:
        s (str): The string to validate.

    Returns:
        str: The original string if valid.

    Raises:
        ValueError: If the string contains any spaces.
    """
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

class SlackResponse(BaseModel):
    response_type: str
    text: Optional[str] = None
    blocks: Optional[List[Dict[str, Any]]] = None

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

class KudosRequest(BaseModel):
    to_user: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=200)