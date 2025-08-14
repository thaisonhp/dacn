from pydantic import BaseModel

# ----------------------------------------


class CreateConversation(BaseModel):
    chat_model: str
    user: str


class ListConversationOut(BaseModel):
    conversation_id: str
    chat_model: str
    user: str
    status: str
    openai_conversation_id: str | None = None
    share: bool = False
    name: str | None = None
    deleted: bool = False
    createdAt: str
    updatedAt: str
