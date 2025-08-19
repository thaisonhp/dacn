from datetime import datetime
from typing import Literal, Optional

import pytz
from bunnet import Document, PydanticObjectId
from pydantic import Field


# -------------------------------------------------
class History(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")  # ⚡ fix lỗi _id
    conversation_id: PydanticObjectId
    question: str = None
    answer: str = None
    refer: list = []
    files: list = []
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    )
    response_time_stream: Optional[float] = None
    response_time: Optional[float] = None
    status: Literal["Success", "Process", "Error"] = "Success"
    request_type: Optional[str] = None
    response_type: Literal["llm", "qa", "error", "voice"] = "llm"
    error_detail: Optional[str] = None
    chatbotId: PydanticObjectId

    class Settings:
        name = "History"
        indexes = ["conversation_id", "chatbotId"]

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        if not self.createdAt:
            self.createdAt = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        return super().save(*args, **kwargs)
