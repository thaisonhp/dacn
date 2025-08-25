from pydantic import BaseModel
from pydantic import BaseModel, Field
from typing import List
from bson import ObjectId
from pydantic import ConfigDict
# ----------------------------------------


class CreateConversation(BaseModel):
    assistant_id: str
    name : str

class Message(BaseModel):
    role: str
    content: str

class MessageOut(BaseModel):
    conversation_id: str
    messages: List[Message]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
