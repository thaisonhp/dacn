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

index_router = APIRouter(prefix="/Index", tags=["Indexing"])


# Create a neural searcher instance
indexer = IndexingPipeline(collection_name=settings.collection_name)


UPLOAD_DIR = Path("file_upload")
UPLOAD_DIR.mkdir(exist_ok=True)


@index_router.post("/api/index")
async def index_file(
    file: UploadFile = File(...),
    knowledge_base_id : List[str] = Query(...)
):
    ids = [ObjectId(kb_id) for kb_id in knowledge_base_id]
    existing = db_sync['knowledge_bases'].find(
        {"_id": {"$in": ids}},
        {"_id": 1}
    ).to_list(length=None)
    existing_ids = [str(doc["_id"]) for doc in existing]
    print(existing)
    missing = [kb_id for kb_id in knowledge_base_id if kb_id not in existing_ids]

    if missing:
        raise HTTPException(status_code=404,
                            detail=f"Các knowledge_base_id sau không tồn tại trong DB: {missing}")
    if file.content_type not in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
    ]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    # Đọc nội dung file vào bytes
    file_content = await file.read()
    file_stream = BytesIO(file_content)
    minio_processor = MinioManager()
    try :
        print("check minio")
        file_path = minio_processor.save_to_minio(file=file,file_stream=file_stream)

    except Exception as e:
        raise HTTPException(status_code= 400, detail="False to save to minio") 
        
    try:
        count = await indexer.add_file(
            file_stream=file_stream, file_path=file_path, knowledge_base_id=knowledge_base_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Indexing failed: {e}")

    return {
        "message": "File uploaded and indexed",
        "filename": file.filename,
        "indexed_chunks": count,
    }
