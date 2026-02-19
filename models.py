from typing import Optional, Annotated
from datetime import datetime
from pydantic import BaseModel, AfterValidator

#function to check if the string is empty or not
def is_empty(s: str):
    if s.strip() == "":
        raise ValueError("Field cannot be empty")
    return s

class Kudos(BaseModel):
    # data model for kudos
    from_user: Annotated[str, AfterValidator(is_empty)]
    to_user: Annotated[str, AfterValidator(is_empty)]
    message: Annotated[str, AfterValidator(is_empty)]
    kudos_id: Optional[int] = None
    time_created: Optional[datetime] = None