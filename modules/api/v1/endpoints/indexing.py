from fastapi import FastAPI
from io import BytesIO
# The file where HybridSearcher is stored
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile ,Query
from utils.indexing import IndexingPipeline
from core.config import settings
from pathlib import Path
from core.config import settings
from utils.manager.file_manager import MinioManager
from typing import List 
from core.config import db_sync , db_async
from bson.objectid import ObjectId
from schema.file import FileCreate, FileUpdate, FileOut
from models.file import File_Model
from bunnet import init_bunnet

index_router = APIRouter(prefix="/Index", tags=["Indexing"])


# Create a neural searcher instance
indexer = IndexingPipeline(collection_name=settings.collection_name)


init_bunnet(database=db_sync, document_models=[File_Model])

@index_router.post("/api/index")
async def index_files(
    files: List[UploadFile] = File(...),
    knowledge_base_id: List[str] = Query(...)
):
    # Check knowledge_base_id
    ids = [ObjectId(kb_id) for kb_id in knowledge_base_id]
    existing = db_sync['knowledge_bases'].find(
        {"_id": {"$in": ids}},
        {"_id": 1}
    ).to_list(length=None)
    existing_ids = [str(doc["_id"]) for doc in existing]

    missing = [kb_id for kb_id in knowledge_base_id if kb_id not in existing_ids]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Các knowledge_base_id sau không tồn tại trong DB: {missing}"
        )

    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
    ]

    minio_processor = MinioManager()
    results = []

    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

        file_content = await file.read()
        file_stream = BytesIO(file_content)

        try:
            file_path = minio_processor.save_to_minio(file=file, file_stream=BytesIO(file_content))
        except Exception:
            raise HTTPException(status_code=400, detail=f"Failed to save {file.filename} to MinIO")

        try:
            count = await indexer.add_file(
                file_stream=BytesIO(file_content),
                file_path=file_path,
                knowledge_base_id=knowledge_base_id
            )
            # them file to mongo db 
            file_name = file_path.split("/")[-1]
            print(file_name)
            result_save_to_mongo = File_Model(
                knowledge_base_id = knowledge_base_id , 
                file_name=file_name,
                file_path = file_path
            )
            result_save_to_mongo.insert()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Indexing failed for {file.filename}: {e}")

        results.append({
            "filename": file.filename,
            "indexed_chunks": count,
        })

    return {
        "message": "Files uploaded and indexed",
        "results": results
    }

@index_router.delete("/api/delete-index")
async def delete_index(
    knowledge_base_id: str = Query(...),
    file_path: str = Query(...),
):
    # 1. Xóa từ Qdrant
    from qdrant_client import QdrantClient, models
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    client.delete(
        collection_name=settings.collection_name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(
                    key="knowledge_base_id",
                    match=models.MatchValue(value=knowledge_base_id)
                )]
            )
        )
    )
    # vectors tied to deleted points gone too :contentReference[oaicite:4]{index=4}

    # 2. Xóa từ MinIO
    from utils.manager.file_manager import MinioManager
    minio = MinioManager()
    bucket, obj_path = file_path.split("/", 1)
    try:
        minio.client.remove_object(bucket, obj_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"MinIO delete failed: {e}")

    return {"message": "Deleted from Qdrant & MinIO."}