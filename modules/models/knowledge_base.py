from datetime import datetime
from typing import Optional
from bunnet import Document, PydanticObjectId
from pydantic import Field
import pytz

class KnowledgeBase(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    user_id: PydanticObjectId = Field(...)  # Tham chiếu đến users.id
    name: str = Field(...)  # Tương ứng với varchar
    description: Optional[str] = None  # Tương ứng với text, có thể null
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))

    class Settings:
        name = "knowledge_bases"
        indexes = ["user_id", "name"]  # Index trên user_id và name để tối ưu tìm kiếm
        note = "KB riêng cho user/workspace"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}