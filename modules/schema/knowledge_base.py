from pydantic import BaseModel
from typing import Optional
from bunnet import PydanticObjectId

class CreateKnowledgeBase(BaseModel):
    name: str
    description: Optional[str] = None