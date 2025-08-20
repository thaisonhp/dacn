import os
from typing import List, Dict
from dotenv import load_dotenv
from utils.parser import MarkItDownParser
from utils.chunker import ParagraphMarkdownChunker
from langchain_community.vectorstores import Qdrant
from core.config import settings
from uuid import uuid4
from datetime import datetime, timezone
from core.config import qd_client , openai_client
from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import PointStruct
from utils.embedder import Embedder
from qdrant_client import QdrantClient, models
# from utils.manager.file_manager import MinioManager
load_dotenv()


class Indexer:
    def __init__(self, collection_name: str = None):
        self.parser = MarkItDownParser()
        self.text_splitter = ParagraphMarkdownChunker()
        self.collection_name = collection_name or settings.collection_name

        self.embeder = Embedder()
        # Init Qdrant client + vectorstore
        self.vectorstore = qd_client

    async def indexing(self, file_path: str , knowledge_base_id: str = None):
        # bo sung logic đẩy file lên minio 
        parsed = self.parser.parse(file_path)
        print(f"✅ Parsed " , parsed)
        chunks = self.text_splitter.chunk(parsed["text"], source_file=file_path)
        texts = [chunk.text for chunk in chunks]
        print(f"✅ Chunked into {len(texts)} texts")
        text_embed = self.embeder.process(texts)
        print("✅ Embedding completed")
        points = [
            PointStruct(
                id=idx,
                vector=data,
                payload={"text": text,
                         "file_name": None ,
                         "knowledge_base_id" : None},
            )
            for idx, (data, text) in enumerate(zip(text_embed, texts))
        ]
    
        self.vectorstore.upsert(
                collection_name=settings.collection_name,
                points=points,
                wait=True
            )
        print(f"✅ Indexed {len(texts)} documents into '{self.collection_name}'")
        # ======= sau khi xong het phan luu vao vector store thi bat dau luu vao minio va lay ra url luu vao db 
        return len(texts)

    async def search(self, query: str, limit: int = 5)->List[str]:
        result = self.vectorstore.query_points(
            collection_name=settings.collection_name,
            query= self.embeder.client.embed_query(query),
            limit=limit,
            # using="default" 
        ).points
        list_text = []
        for item in result:
            text = item.payload.get("text")
            list_text.append(text)
        return list_text
