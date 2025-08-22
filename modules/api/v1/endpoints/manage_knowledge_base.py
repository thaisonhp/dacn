from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends ,Query
from fastapi.responses import JSONResponse, Response
from bson import ObjectId
from bunnet import init_bunnet, PydanticObjectId
from core.config import db_sync , db_async
from models.knowledge_base import KnowledgeBase
from schema.knowledge_base import CreateKnowledgeBase
from typing import List
from core.security import get_current_user_id
import logging

logger = logging.getLogger(__name__)
kb_router = APIRouter(prefix="/knowledge_bases", tags=["Knowledge Bases"])

@kb_router.post("/create")
async def create_knowledge_base(
    data: CreateKnowledgeBase,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """Tạo một knowledge base mới"""
    init_bunnet(database=db_sync, document_models=[KnowledgeBase])

    id = str(ObjectId())
    kb = KnowledgeBase(
        id=id,
        user_id=user_id,
        name=data.name,
        description=data.description
    )
    background_tasks.add_task(kb.insert)
    logger.info(f"Knowledge base {kb.name} created successfully for user {kb.user_id}")
    return JSONResponse(
        status_code=201,
        content={"id": id, "message": "Knowledge base created successfully"}
    )

@kb_router.put("/update/{kb_id}")
async def update_knowledge_base(
    kb_id: str,
    data: CreateKnowledgeBase,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)
):
    """Cập nhật một knowledge base"""
    init_bunnet(database=db_sync, document_models=[KnowledgeBase])
    kb = KnowledgeBase.get(kb_id).run()

    if not kb:
        logger.error(f"Knowledge base {kb_id} not found")
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if str(kb.user_id) != user_id:
        logger.warning(f"User {user_id} attempted to update KB {kb_id} owned by {kb.user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to update this knowledge base")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(kb, key, value)

    background_tasks.add_task(kb.save)
    logger.info(f"Knowledge base {kb.name} updated successfully for user {kb.user_id}")
    return Response(status_code=200, content="Knowledge base updated successfully")

@kb_router.get("/list")
async def list_knowledge_bases_by_user(current_user_id: str = Depends(get_current_user_id)):
    """Lấy danh sách knowledge bases của một user"""
    cursor = db_sync['knowledge_bases'].find({"user_id": ObjectId(current_user_id)})
    kbs = cursor.to_list(length=None)

    if not kbs:
        raise HTTPException(status_code=404, detail="Không tìm thấy knowledge base nào cho user này.")

    # Convert ObjectId -> str để JSON hóa được
    for kb in kbs:
        kb["_id"] = str(kb["_id"])
        if isinstance(kb.get("user_id"), ObjectId):
            kb["user_id"] = str(kb["user_id"])

    return kbs

@kb_router.delete("/delete/{kb_id}")
async def delete_knowledge_base(kb_id: str, user_id: str = Depends(get_current_user_id)):
    """Xóa một knowledge base"""
    init_bunnet(database=db_sync, document_models=[KnowledgeBase])
    kb = KnowledgeBase.get(kb_id).run()
    if not kb:
        logger.error(f"Knowledge base {kb_id} not found")
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if str(kb.user_id) != user_id:
        logger.warning(f"User {user_id} attempted to delete KB {kb_id} owned by {kb.user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this knowledge base")

    kb.delete()
    logger.info(f"Knowledge base {kb_id} deleted successfully for user {user_id}")
    return Response(status_code=200, content="Knowledge base deleted successfully")

@kb_router.get("/get")
async def get_knowledge_bases(kb_name: List[str] = Query(...)):
    """Lấy thông tin chi tiết của nhiều knowledge base"""
    init_bunnet(database=db_sync, document_models=[KnowledgeBase])

    mongo_kbs = await db_async["knowledge_bases"].find(
        {"name": {"$in": kb_name}}
    ).to_list(length=None)
    print(mongo_kbs)
    if not mongo_kbs:
        raise HTTPException(status_code=404, detail="Không tìm thấy knowledge_bases")
    list_kb_id = [] 
    for item in mongo_kbs :
        list_kb_id.append(str(item.get('_id')))
    return JSONResponse(
        content={
            "status" : "success",
            "list_kb_id" : list_kb_id
        }
    )