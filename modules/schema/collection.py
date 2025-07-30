from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional 
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models

class Collection(BaseModel):
    client: QdrantClient = Field(default_factory=lambda: QdrantClient(), description="Qdrant client instance")
    name: str = Field(..., description="The name of the collection")
    embedding_model: str = Field(..., description="The embedding model to use")
    metadata: Optional[dict] = Field(None, description="Additional metadata for the collection")
