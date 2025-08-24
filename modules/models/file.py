from datetime import datetime
from typing import Optional , List
import pytz
from bunnet import Document, PydanticObjectId
from pydantic import Field

class File_Model(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    knowledge_base_id: Optional[List[str]] = None
    file_name: str
    file_type: Optional[str] = None
    file_path: str
    size_kb: Optional[int] = None
    uploaded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")))

    class Settings:
        name = "files"
        indexes = ["workspace_id", "file_name"]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def save(self, *args, **kwargs):
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        self.updated_at = datetime.now(tz)
        if not self.uploaded_at:
            self.uploaded_at = datetime.now(tz)
        return super().save(*args, **kwargs)
