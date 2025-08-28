from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from bunnet import init_bunnet
from core.config import db_sync ,db_async , minio_client
from models.file import File_Model
from schema.file import FileCreate, FileUpdate, FileOut
from datetime import timedelta ,datetime
from fastapi import APIRouter, HTTPException
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from bson import ObjectId


file_router = APIRouter(prefix="/files", tags=["Files"])

# Init bunnet
init_bunnet(database=db_sync, document_models=[File_Model])

@file_router.get("/", response_model=List[FileOut])
async def list_files():
    cursor = db_async["files"].find({})   # find_all() ❌ → find({})
    docs = await cursor.to_list(length=None)
    return [FileOut(**doc) for doc in docs]

@file_router.get("/files/by-knowledge-base/{kb_id}", response_model=List[FileOut])
async def get_files_by_kb(kb_id: str):
    try:
        # check kb_id hợp lệ (ObjectId string)
        if not ObjectId.is_valid(kb_id):
            raise HTTPException(status_code=400, detail="Invalid knowledge_base_id")

        docs = await db_async["files"].find(
            {"knowledge_base_id": kb_id}
        ).to_list(length=None)

        if not docs:
            raise HTTPException(status_code=404, detail="No files found for this knowledge_base_id")

        return [FileOut(**doc) for doc in docs]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")

@file_router.get("/{file_id}", response_model=FileOut)
async def get_file(file_id: str):
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file_id")

    doc = await db_async["files"].find_one({"_id": ObjectId(file_id)})

    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    return FileOut(**doc)

@file_router.put("/{file_id}", response_model=FileOut)
async def rename_file(file_id: str, new_name: str):
    # check ObjectId hợp lệ
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file_id")

    # chỉ update file_name + updated_at
    update_data = {
        "file_name": new_name,
        "updated_at": datetime.utcnow()
    }

    # update doc trong db
    result = await db_async["files"].find_one_and_update(
        {"_id": ObjectId(file_id)},
        {"$set": update_data},
        return_document=True  # lấy doc sau khi update
    )

    if not result:
        raise HTTPException(status_code=404, detail="File not found")

    # convert ObjectId -> str
    result["_id"] = str(result["_id"])

    return FileOut(**result)


@file_router.delete("/{file_id}")
async def delete_file(file_id: str):
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file_id")

    result = await db_async["files"].delete_one({"_id": ObjectId(file_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")

    return JSONResponse(content={"message": "File deleted successfully"})


@file_router.get("/preview/{file_path:path}")
async def preview_file(file_path: str):
    try:
        # file_path ví dụ: "origin/7_TH1.docx"
        url = minio_client.presigned_get_object(
            bucket_name="chatbot-embeddings",
            object_name=file_path.split("/")[-1],
            expires=timedelta(hours=1)   # link sống trong 1 tiếng
        )
        return {"preview_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không tạo được preview URL: {e}")

