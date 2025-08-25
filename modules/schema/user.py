from pydantic import BaseModel
from bunnet import Document, PydanticObjectId
from typing import List , Optional
from datetime import datetime
from pydantic import Field
from pydantic import BaseModel, EmailStr
from typing import Literal

# ---- Pydantic schema để validate input/output ----
class UserCreate(BaseModel):
    full_name: str
    email: str
    avatar_url: str | None = None

class UserUpdate(BaseModel):
    full_name: str | None = None
    username : str | None = None 
    role : Literal["user", "admin"] = "user" 
class UserOut(BaseModel):
    id: str
    username : str
    full_name: str
    email: str
    role : str
    created_at: datetime
    updated_at: datetime