from pydantic import BaseModel
from bunnet import Document, PydanticObjectId
from typing import List , Optional
from datetime import datetime
from pydantic import Field
from pydantic import BaseModel, EmailStr

class SignupSchema(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    otp_code: Optional[str] = None
    password: str
    role: Optional[str] = None
    google_id: Optional[str] = None



class LoginSchema(BaseModel):
    username_or_email: str
    password: str