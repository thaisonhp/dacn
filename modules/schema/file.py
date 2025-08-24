from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FileCreate(BaseModel):
    workspace_id: Optional[str] = None
    file_name: str
    file_path: str
    size_kb: Optional[int] = None

class FileUpdate(BaseModel):
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    workspace_id: Optional[str] = None

class FileOut(BaseModel):
    id: str
    workspace_id: Optional[str]
    file_name: str
    file_path: str
    uploaded_at: Optional[datetime]
    updated_at: Optional[datetime]
