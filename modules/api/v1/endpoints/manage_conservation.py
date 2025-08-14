from datetime import datetime
from typing import Optional

from bson import ObjectId
from bunnet import init_bunnet
from core.config import db_async, db_sync
from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, paginate
from models.conversatition import Conversation
from models.history import History
from schema.conversation import CreateConversation, ListConversationOut

# -------------------------------------------------------

conversation_router = APIRouter(prefix="/history", tags=["History"])


def clean_conversation_item(item):
    if "_id" in item:
        item["conversation_id"] = str(item["_id"])
        del item["_id"]
    if "conversation_id" in item:
        item["conversation_id"] = str(item["conversation_id"])
    if "chatbotId" in item:
        item["chatbotId"] = str(item["chatbotId"])
    for field in ("createdAt", "updatedAt"):
        if field in item and isinstance(item[field], datetime):
            item[field] = item[field].isoformat()
    return item


@conversation_router.post("/conversation/create")
async def create_conversation(
    data: CreateConversation, background_tasks: BackgroundTasks
):
    init_bunnet(database=db_sync, document_models=[Conversation])
    id = ObjectId()
    conversation = Conversation(
        chat_model=data.chat_model,
        user=data.user,
        id=str(id),
    )
    background_tasks.add_task(conversation.insert)
    return JSONResponse(
        status_code=200,
        content={"id": str(id), "message": "Conversation created successfully."},
    )


@conversation_router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    conversation = (
        await db_async["History"]
        .find({"conversation_id": ObjectId(conversation_id)})
        .to_list()
    )
    if conversation:
        return [clean_conversation_item(item) for item in conversation]
    return JSONResponse(status_code=404, content={"message": "Conversation not found."})


@conversation_router.get("/conversation/list")
async def list_conversations(
    user: str = Query(...), chat_model: str = Query(...)
) -> Page[ListConversationOut]:

    conversations = (
        await db_async["Conversation"]
        .find({"user": user, "deleted": False, "chat_model": chat_model})
        .sort("createdAt", -1)
        .to_list()
    )
    return paginate([clean_conversation_item(item) for item in conversations])


@conversation_router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    result = await db_async["Conversation"].update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {"deleted": True, "updatedAt": datetime.now()}},
    )
    if result.matched_count == 0:
        return JSONResponse(
            status_code=404, content={"message": "Conversation not found."}
        )
    return JSONResponse(
        status_code=200, content={"message": "Conversation deleted successfully."}
    )
