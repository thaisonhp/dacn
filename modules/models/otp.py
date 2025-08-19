from datetime import datetime, timedelta
from typing import Optional
from bunnet import Document, PydanticObjectId
from pydantic import Field, EmailStr
import pytz

class OtpCode(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    email: EmailStr
    otp: str
    expiresAt: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC) + timedelta(minutes=5))  
    createdAt: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))

    class Settings:
        name = "otp_codes"
        # TTL index tự động xóa document sau khi hết hạn
        indexes = ["email", "otp"]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
