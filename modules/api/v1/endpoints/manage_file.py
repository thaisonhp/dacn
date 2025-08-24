from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from bunnet import init_bunnet
from core.config import db_sync
from models.file import File_Model
from schema.file import FileCreate, FileUpdate, FileOut

file_router = APIRouter(prefix="/files", tags=["Files"])

# Init bunnet
init_bunnet(database=db_sync, document_models=[File_Model])

@file_router.post("/", response_model=FileOut)
async def create_file(data: FileCreate):
    file = File_Model(**data.dict())
    await file.insert()
    return FileOut(**file.model_dump(by_alias=True))

@file_router.get("/", response_model=List[FileOut])
async def list_files():
    docs = await File_Model.find_all().to_list()
    return [FileOut(**doc.model_dump(by_alias=True)) for doc in docs]

@file_router.get("/{file_id}", response_model=FileOut)
async def get_file(file_id: str):
    doc = await File_Model.get(file_id)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    return FileOut(**doc.model_dump(by_alias=True))

@file_router.put("/{file_id}", response_model=FileOut)
async def update_file(file_id: str, data: FileUpdate):
    doc = await File_Model.get(file_id)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    update_data = data.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(doc, k, v)
    await doc.save()
    return FileOut(**doc.model_dump(by_alias=True))

@file_router.delete("/{file_id}")
async def delete_file(file_id: str):
    doc = await File_Model.get(file_id)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    await doc.delete()
    return JSONResponse(content={"message": "File deleted successfully"})


