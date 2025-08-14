from pydantic import BaseModel


class CreateChatModel(BaseModel):
    vector_store_id: list[str] = []
    library_id: list[str] = []
    mcp_server: bool = False
    qa: list[str] = []
    model: str = "gpt-4o-mini"
    name: str = None
    owner: str
    prompt: str = None
    chatbot_id: str
    max_doc: int = 20
    temperature: float = 0.2
