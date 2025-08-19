from pydantic import BaseModel
from bunnet import Document, PydanticObjectId
from typing import List , Optional
from datetime import datetime
from pydantic import Field

class CreateChatModel(BaseModel):
    model: str = "gpt-4o-mini"
    name: str = None
    description_assistant: str = None
    temperature: float = 0.2
    opening_greeting : str = None 
    list_knowledge_base_id : List[PydanticObjectId]
    prompt: str = None
    max_doc: int = 20
    createdAt: Optional[datetime] = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = Field(default_factory=datetime.now)

