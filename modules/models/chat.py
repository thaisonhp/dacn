from datetime import datetime
from typing import List, Optional

import pytz
from bunnet import Document, PydanticObjectId
from pydantic import Field

# ----------------------------------------------


class ChatModel(Document):
    id: PydanticObjectId
    vector_store_id: List[str] = []
    library_id: List[str] = []
    qa: List[str] = []
    mcp_server: bool = False
    name: str = None
    model: str = "gpt-4o-mini"
    owner: str
    prompt: str = None
    chatbot_id: str
    max_doc: int = 20
    temperature: float = 0.2
    createdAt: Optional[datetime] = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = Field(default_factory=datetime.now)

    class Settings:
        name = "chat_models"
        indexes = ["owner", "chatbot_id"]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        if not self.createdAt:
            self.createdAt = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        return super().save(*args, **kwargs)
