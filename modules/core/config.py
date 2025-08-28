from pydantic_settings import BaseSettings
from typing import Optional, List
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    VectorParams,
)
from enum import Enum
from miniopy_async import Minio
import openai
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bunnet import init_bunnet
from dotenv import load_dotenv
from loguru import logger
from openai import AsyncOpenAI
from qdrant_client.models import Distance, VectorParams, models
from fastembed import TextEmbedding, LateInteractionTextEmbedding, SparseTextEmbedding 
load_dotenv()


class Settings(BaseSettings):
    qdrant_url: str = os.getenv("QDRANT_URL")
    qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY")
    collection_name: str = os.getenv("COLLECTION_NAME")
    embedding_dimension: int = os.getenv("EMBEDDING_DIMENSION", 128)
    distance_metric: str = os.getenv("DISTANCE_METRIC", "COSINE")
    metadata: Optional[dict] = os.getenv("METADATA", None)
    # dense_vector_name: str = os.getenv("DENSE_VECTOR_NAME", "dense")
    # sparse_vector_name: str = os.getenv("SPARSE_VECTOR_NAME", "sparse")

    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "testdb")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    # Các biến môi trường khác nếu cần thiết
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key : str = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key : str = os.getenv("MINIO_SECRET_KEY")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "mybucket")
    secret_key : str = os.getenv("SECRET_KEY","None")
    google_client_id: str =os.getenv("GOOGLE_CLIENT_ID"),
    google_client_secret: str =os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_uri: str = os.getenv("REDIRECT_URI",None)
    SESSION_SECRET_KEY : str = os.getenv("SESSION_SECRET_KEY",None)
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
# khoi tao QdrantClient
# Map model -> embedding dimension
MODEL_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,           # sentence-transformers/all-MiniLM-L6-v2
    "colbertv2.0": 128,                # tùy training, nhiều bản dùng 128
}

qd_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key ,timeout=300)
dense_embedding_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
bm25_embedding_model = SparseTextEmbedding("Qdrant/bm25")
late_interaction_embedding_model = LateInteractionTextEmbedding("colbert-ir/colbertv2.0")
collections = [c.name for c in qd_client.get_collections().collections]
if "hybrid-search" not in collections:
    qd_client.create_collection(
        "hybrid-search",
        vectors_config={
            "all-MiniLM-L6-v2": models.VectorParams(
                size=MODEL_DIMENSIONS["all-MiniLM-L6-v2"],
                distance=models.Distance.COSINE,
            ),
            "colbertv2.0": models.VectorParams(
                size=MODEL_DIMENSIONS["colbertv2.0"],
                distance=models.Distance.COSINE,
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM,
                ),
                hnsw_config=models.HnswConfigDiff(m=0)
            ),
        },
        sparse_vectors_config={
            "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)
        }
    )
else:
    print("Collection 'hybrid-search' đã tồn tại, bỏ qua tạo mới")
qd_client.create_payload_index(
            collection_name=settings.collection_name,
            field_name="knowledge_base_id",
            field_schema="keyword"  # vì ID dạng chuỗi
        )
# Cấu hình logger
handler = logging.StreamHandler()
# hoặc có thể dùng SysLogHandler...
logger.add(handler)

openai_client = openai.Client(api_key=settings.openai_api_key)
openai_async_client = AsyncOpenAI(api_key=settings.openai_api_key)



db_sync_client = MongoClient(settings.mongodb_uri)
db_sync = db_sync_client[settings.mongodb_db]
db_async_client = AsyncIOMotorClient(settings.mongodb_uri)
db_async = db_async_client[settings.mongodb_db]


minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=True,
)


class MediaType(Enum):
    image = "image"
    document = "document"





# # Gắn sẵn hàm init bunnet (tùy code chạy sync hay async)
# async def init_mongo():
#     from models.chat import ChatModel
#     from models.conversatition import Conversation
#     from models.history import History  # import các document

#     await init_bunnet(database=mongo_db, document_models=[ChatModel, Conversation, History])

# import asyncio
# asyncio.run(init_mongo())
