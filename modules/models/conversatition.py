from datetime import datetime
from typing import Literal, Optional

import pytz
from bunnet import Document, PydanticObjectId
from pydantic import Field

# -------------------------------------------------


class Conversation(Document):
    id: PydanticObjectId
    chat_model: str
    user: str
    status: Literal["activate", "inactivate", "delete"] = "activate"
    openai_conversation_id: str | None = None
    share: bool = False
    name: str | None = None
    deleted: bool = False
    createdAt: Optional[datetime] = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = Field(default_factory=datetime.now)

    class Settings:
        name = "Conversation"
        indexes = ["chat_model"]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    async def save(self, *args, **kwargs):
        self.updatedAt = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        if not self.createdAt:
            self.createdAt = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        return await super().save(*args, **kwargs)
