from pydantic import BaseModel
from bunnet import Document, PydanticObjectId
from typing import List , Optional
from datetime import datetime
from pydantic import Field

class CreateAsisstant(BaseModel):
    assistant_name: str                      # bắt buộc
    system_prompt: str                       # bắt buộc
    model: str                               # bắt buộc  
    description_assistant: Optional[str] = None
    opening_greeting: Optional[str] = None
    list_knowledge_base_id: Optional[List[PydanticObjectId]] = []
    temperature: float = 0.2
    top_p: float = 0.5
    max_doc: int = 20
    createdAt: Optional[datetime] = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = Field(default_factory=datetime.now)

