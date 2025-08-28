from __future__ import annotations
from functools import cached_property
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import SentenceTransformer
from core.config import settings, dense_embedding_model, bm25_embedding_model, late_interaction_embedding_model
from qdrant_client.models import Distance, VectorParams, models


class Embedder:
    def __init__(self, backend: str = "local"):
        """
        backend: "openai" hoặc "local"
        """
        if backend not in ["openai", "local"]:
            raise ValueError("❌ backend phải là 'openai' hoặc 'local'")
        self.backend = backend

    @cached_property
    def openai_client(self):
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )

    @cached_property
    def local_model(self):
        return SentenceTransformer("huyydangg/DEk21_hcmute_embedding")

    def embed_documents(self, docs: list[str]):
        """
        Embedding cho indexing (list chunks).        return [item.payload.get("text") for item in result]
        """
        if self.backend == "openai":
            return self.openai_client.embed_documents(docs)
        elif self.backend == "local":
            dense_embeddings = list(dense_embedding_model.embed(doc for doc in docs))
            bm25_embeddings = list(bm25_embedding_model.embed(doc for doc in docs))
            late_interaction_embeddings = list(late_interaction_embedding_model.embed(doc for doc in docs))
            return (
                dense_embeddings,
                bm25_embeddings,
                late_interaction_embeddings
            )
            

    def embed_query(self, query: str):
        """
        Embedding cho query (single string).
        """
        if self.backend == "openai":
            return self.openai_client.embed_query(query)
        elif self.backend == "local":
            dense_vectors = next(dense_embedding_model.query_embed(query))
            sparse_vectors = next(bm25_embedding_model.query_embed(query))
            late_vectors = next(late_interaction_embedding_model.query_embed(query))
            
            return {
                "dense": dense_vectors,
                "bm25": sparse_vectors,
                "late": late_vectors
            }
