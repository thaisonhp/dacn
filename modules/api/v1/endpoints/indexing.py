from fastapi import FastAPI

# The file where HybridSearcher is stored
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from utils.indexing import IndexingPipeline
from core.config import settings
from pathlib import Path
from core.config import settings
from utils.manager.file_manager import MinioManager
index_router = APIRouter(prefix="/Index", tags=["Indexing"])


# Create a neural searcher instance
indexer = IndexingPipeline(collection_name=settings.collection_name)


UPLOAD_DIR = Path("file_upload")
UPLOAD_DIR.mkdir(exist_ok=True)


@index_router.post("/api/index")
async def index_file(
    file: UploadFile = File(...)
):
    if file.content_type not in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
    ]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    # Index file vào Qdrant
    minio_processor = MinioManager()
    # minio_processor.save_to_minio(file=file,file_stream=)
    try:
        count = await indexer.add_file(
            file_path=str(file_path)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Indexing failed: {e}")

    return {
        "message": "File uploaded and indexed",
        "filename": file.filename,
        # "tenant_id": tenant_id,
        "indexed_chunks": count,
    }
