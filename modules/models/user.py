from datetime import datetime
from typing import Literal, Optional

import pytz
from bunnet import Document, PydanticObjectId
from pydantic import Field, EmailStr
import bcrypt


class User(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")  # ⚡ fix lỗi _id
    full_name: Optional[str] = None
    username: str | None 
    email: EmailStr
    password_hash: Optional[str] = None
    role: Literal["user", "admin"] = "user"
    is_verified: bool = False
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    )

    class Settings:
        name = "users"
        indexes = ["username", "email", "google_id"]

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        if not self.created_at:
            self.created_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        return super().save(*args, **kwargs)

    # --------- helper methods ----------
    def set_password(self, password: str):
        """Hash password và lưu vào password_hash"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Kiểm tra password"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))
    
    def from_dict(cls, data: dict):
        return cls(
            _id=data.get("_id"),
            username=data.get("username"),
            email=data.get("email"),
            full_name=data.get("full_name"),
            password_hash=data.get("password_hash"),
            avatar_url=data.get("avatar_url"),
            role=data.get("role", "user"),
            is_verified=data.get("is_verified", False),
            google_id=data.get("google_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


    def to_dict(self, include_email=True, include_role=True):
        """Convert document thành dict, bỏ password_hash"""
        data = {
            "id": str(self.id),
            "full_name": self.full_name,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "is_verified": self.is_verified,
            "google_id": self.google_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_email:
            data["email"] = self.email
        if include_role:
            data["role"] = self.role
        return data
