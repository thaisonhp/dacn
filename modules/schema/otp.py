from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta


class CreateOtpCode(BaseModel):
    email: EmailStr
    otp: str
    expiresAt: datetime = Field(default_factory=lambda: datetime.now() + timedelta(minutes=5))
    createdAt: Optional[datetime] = Field(default_factory=datetime.now)
