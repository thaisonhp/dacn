from datetime import datetime
from typing import Optional

from bson import ObjectId
from bunnet import init_bunnet
from core.config import db_async, db_sync
from fastapi import APIRouter, BackgroundTasks, Query , HTTPException
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, paginate
from models.conversatition import Conversation
from models.history import History
from schema.conversation import CreateConversation, ListConversationOut

# -------------------------------------------------------

conversation_router = APIRouter(prefix="/history", tags=["History"])


def clean_conversation_item(item):
    # Map _id -> conversation_id
    if "_id" in item:
        item["conversation_id"] = str(item["_id"])
        del item["_id"]

    # Ensure assistant_id is string
    if "assistant_id" in item:
        item["assistant_id"] = str(item["assistant_id"])

    # Convert datetime fields
    for field in ("createdAt", "updatedAt"):
        if field in item and isinstance(item[field], datetime):
            item[field] = item[field].isoformat()

    # Chỉ giữ lại các field cần thiết
    cleaned_item = {
        "conversation_id": item.get("conversation_id"),
        "assistant_id": item.get("assistant_id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "openai_conversation_id": item.get("openai_conversation_id"),
        "share": item.get("share"),
        "deleted": item.get("deleted"),
        "createdAt": item.get("createdAt"),
        "updatedAt": item.get("updatedAt"),
    }

    return cleaned_item

@conversation_router.post("/conversation/create")
async def create_conversation(
    data: CreateConversation, background_tasks: BackgroundTasks
):
    
    init_bunnet(database=db_sync, document_models=[Conversation])
    chat_model = await db_async["chat_models"].find_one(
        {"_id": ObjectId(data.assistant_id)}
    )
    if not chat_model:
        raise HTTPException(status_code=404, detail="Chat model not found.")
    id = ObjectId()
    conversation = Conversation(
        assistant_id=data.assistant_id,
        id=str(id),
        name=data.name
    )
    background_tasks.add_task(conversation.insert)
    return JSONResponse(
        status_code=200,
        content={"id": str(id), "message": "Conversation created successfully."},
    )


@conversation_router.get("/all")
async def get_all_conversations():
    conversations = await db_async["Conversation"].find({}).to_list(length=None)

    if not conversations:
        return JSONResponse(status_code=404, content={"message": "No conversations found."})

    return [clean_conversation_item(item) for item in conversations]

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


@conversation_router.get("/conversation/list_answer")
async def list_conversations(
    # user: str = Query(...), chat_model: str = Query(...)
    conversation_id: str
) -> Page[ListConversationOut]:
    conversations = (
        await db_async["History"]
        .find({"conversation_id": ObjectId(conversation_id)})
        .to_list()
    )
    print(conversations)

    return paginate([(item) for item in conversations])


@conversation_router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    result = await db_async["Conversation"].delete_one(
        {"_id": ObjectId(conversation_id)}
    )
    if result.deleted_count == 0:
        return JSONResponse(
            status_code=404, content={"message": "Conversation not found."}
        )
    return JSONResponse(
        status_code=200, content={"message": "Conversation deleted successfully."}
    )


@conversation_router.get("/conversation/by-id/{conversation_id}")
async def get_conversation_by_id(conversation_id: str):
    conversation = await db_async["Conversation"].find_one({"_id": ObjectId(conversation_id)})
    if not conversation:
        return JSONResponse(status_code=404, content={"message": "Conversation not found."})
    return clean_conversation_item(conversation)

@conversation_router.get("/conversation/by-assistant/{assistant_id}")
async def get_conversation_by_assistant_id(assistant_id: str):
    conversations = await db_async["Conversation"].find({"assistant_id": assistant_id}).to_list(length=None)
    
    if not conversations:
        return JSONResponse(
            status_code=404, content={"message": "No conversations found."}
        )
    
    return [clean_conversation_item(item) for item in conversations]