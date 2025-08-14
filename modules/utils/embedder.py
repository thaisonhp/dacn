from __future__ import annotations
from functools import cached_property
from langchain_openai import OpenAIEmbeddings
from core.config import settings

class Embedder:
    @cached_property
    def client(self):
        return OpenAIEmbeddings(
            model= settings.embedding_model,
            openai_api_key= settings.openai_api_key,
        )

    def process(self, input):
        if not input:
            raise ValueError("❌ list_chunk không được rỗng khi embed")
        embeds = self.client.embed_documents(texts=input)
        return embeds
