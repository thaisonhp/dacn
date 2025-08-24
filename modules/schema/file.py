from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class FileCreate(BaseModel):
    file_name: str
    file_path: str
    know_ledgebase_id: List[str]
    size_kb: Optional[int] = None


class FileUpdate(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    workspace_id: Optional[str] = None


class FileOut(BaseModel):
    id: str = Field(alias="_id")
    file_name: str
    file_path: str
    knowledge_base_id: Optional[List[str]] = Field(default_factory=list, alias="knowledge_base_id")
    uploaded_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {
        "populate_by_name": True  # cho phép map alias _id -> id
    }

    # validator: convert ObjectId -> str
    @field_validator("id", mode="before")
    def convert_objectid(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v
