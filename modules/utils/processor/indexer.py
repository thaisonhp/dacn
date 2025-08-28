import os
from typing import List, Dict
from dotenv import load_dotenv
from utils.parser import MarkItDownParser
from utils.chunker import ParagraphMarkdownChunker
from langchain_community.vectorstores import Qdrant
from core.config import settings
from uuid import uuid4
from datetime import datetime, timezone
from core.config import qd_client, openai_client
from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import PointStruct
from utils.embedder import Embedder
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, LateInteractionTextEmbedding, SparseTextEmbedding 
load_dotenv()


class Indexer:
    def __init__(self, collection_name: str = None, backend: str = "local"):
        self.parser = MarkItDownParser()
        self.text_splitter = ParagraphMarkdownChunker()
        self.collection_name = collection_name or settings.collection_name

        # chọn embedder
        self.embeder = Embedder(backend)
        self.backend = backend

        # Init Qdrant client
        self.vectorstore = qd_client

    async def indexing(self, file_stream, file_path, knowledge_base_id: list[str] = None):
        parsed = self.parser.parse(file_stream)
        # print(f"✅ Parsed ", parsed)
        chunks = self.text_splitter.chunk(parsed["text"], source_file=file_path)
        texts = [chunk.text for chunk in chunks]
        # print(f"✅ Chunked into {len(texts)} texts")

        # embed khác nhau theo backend
        if self.backend == "openai":
            text_embed = self.embeder.embed_documents(texts)  # 1536 dim
        else:
            dense_embeddings,bm25_embeddings,late_interaction_embeddings = self.embeder.embed_documents(texts)  # 768 dim

        print("✅ Embedding completed")

        points = []
        for idx, (dense_embedding, bm25_embedding, late_interaction_embedding, doc) in enumerate(zip(dense_embeddings, bm25_embeddings, late_interaction_embeddings, texts)):
        
            point = PointStruct(
                id=str(uuid4()),
                vector={
                    "all-MiniLM-L6-v2": dense_embedding,
                    "bm25": bm25_embedding.as_object(),
                    "colbertv2.0": late_interaction_embedding,
                },
                payload={
                    "doc" : doc ,
                    "knowledge_base_id": knowledge_base_id}
            )
            points.append(point)

        # operation_info = qd_client.upsert(
        #     collection_name="hybrid-search",
        #     points=points
        # )
        BATCH_SIZE = 20  # safe limit (có thể chỉnh lên 200 nếu text ngắn)
        ful_operation_info = []
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            operation_info = qd_client.upsert(
                collection_name= settings.collection_name,
                points=batch,
                wait=True
            )
            ful_operation_info.append(operation_info)
            print(f"🚀 Upserted batch {i//BATCH_SIZE + 1} ({len(batch)} docs)")
        print(f"✅ Indexed {len(texts)} documents into '{self.collection_name}'")
        return ful_operation_info

    async def search(
        self, query: str, limit: int = 3, knowledge_base_id: List[str] = None
    ) -> List[str]:
        # filter_cond = None
        # if knowledge_base_id:
        #     filter_cond = models.Filter(
        #         should=[
        #             models.FieldCondition(
        #                 key="knowledge_base_id", match=models.MatchValue(value=kb_id)
        #             )
        #             for kb_id in knowledge_base_id
        #         ]
        #     )

        # Embed query theo backend
        if self.backend == "openai":
            query_vec = self.embeder.embed_query(query)
        else:  # local
            input_embeded_result = self.embeder.embed_query(query)
            prefetch = [
            models.Prefetch(
                query=input_embeded_result.get("dense"),
                using="all-MiniLM-L6-v2",
                limit=20,
                ),
            models.Prefetch(
                query=models.SparseVector(**input_embeded_result.get("bm25").as_object()),
                using="bm25",
                limit=20,
                ),
            ]
            results = qd_client.query_points(
                    "hybrid-search",
                    prefetch=prefetch,
                    query=input_embeded_result.get("late"),
                    using="colbertv2.0",
                    with_payload=True,
                    limit=limit,
            )
            return results

       

