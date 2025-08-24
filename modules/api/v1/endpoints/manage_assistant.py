from bson import ObjectId
from bunnet import init_bunnet
from core.config import db_async, db_sync, settings
from fastapi import APIRouter, BackgroundTasks, HTTPException ,Depends
from fastapi.responses import JSONResponse, Response
from models.chat_model import Asisstant
from schema.chat_model import CreateAsisstant
from schema.promt_engine import PromtEngine
from schema.model_setting import ModelSetting
from bunnet import PydanticObjectId
from core.security import get_current_user_id
from datetime import datetime

# -------------------------------------------------
chat_model_router = APIRouter(prefix="/chat-model", tags=["Chat Model"])

def clean_assistant(item):
    cleaned = {}

    if "_id" in item:
        cleaned["_id"] = str(item["_id"])
    if "user_id" in item:
        cleaned["user_id"] = str(item["user_id"])
    if "asistant_name" in item:
        cleaned["asistant_name"] = item["asistant_name"]
    if "decription_assistant" in item:
        cleaned["decription_assistant"] = item["decription_assistant"]
    if "opening_greeting" in item:
        cleaned["opening_greeting"] = item["opening_greeting"]
    if "list_knowledge_base_id" in item:
        cleaned["list_knowledge_base_id"] = [str(x) for x in item.get("list_knowledge_base_id", [])]
    if "model" in item:
        cleaned["model"] = item["model"]
    if "system_prompt" in item:
        cleaned["system_prompt"] = item["system_prompt"]
    if "max_doc" in item:
        cleaned["max_doc"] = item["max_doc"]
    if "temperature" in item:
        cleaned["temperature"] = item["temperature"]
    if "top_p" in item:
        cleaned["top_p"] = item["top_p"]

    # Nếu có createdAt, updatedAt thì format ISO như conversation
    for field in ("createdAt", "updatedAt"):
        if field in item and isinstance(item[field], datetime):
            cleaned[field] = item[field].isoformat()

    return cleaned
@chat_model_router.post("/create")
async def create_chat_model(data: CreateAsisstant, background_tasks: BackgroundTasks ,user_id : str = Depends(get_current_user_id) ):
    init_bunnet(database=db_sync, document_models=[Asisstant])
    id = str(ObjectId())
    chat_model = Asisstant(
        user_id=user_id,
        asistant_name=data.assistant_name,
        decription_assistant =data.description_assistant,
        opening_greeting=data.opening_greeting,
        list_knowledge_base_id=data.list_knowledge_base_id,
        model=data.model,
        system_prompt =data.system_prompt,
        max_doc=data.max_doc,
        temperature=data.temperature,
        top_p = data.top_p
    )
    background_tasks.add_task(chat_model.insert)
    return JSONResponse(
        status_code=201,
        content={"id": id, "message": "Chat model created successfully."},
    )


@chat_model_router.put("/update/{chat_model_id}")
async def update_chat_model(
    chat_model_id: str, data: CreateAsisstant, background_tasks: BackgroundTasks
):
    init_bunnet(database=db_sync, document_models=[Asisstant])
    chat_model = Asisstant.get(chat_model_id).run()

    if not chat_model:
        raise HTTPException(status_code=404, detail="Chat model not found.")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(chat_model, key, value)

    background_tasks.add_task(chat_model.save)
    return Response(status_code=200, content="Chat model updated successfully.")

@chat_model_router.get("/all")
async def get_all_assistant():
    list_assistant = await db_async["chat_models"].find({}).to_list(length=None)

    if not list_assistant:
        return JSONResponse(status_code=404, content={"message": "No conversations found."})

    return [clean_assistant(item) for item in list_assistant]
@chat_model_router.get("/list/{owner}")
async def list_chat_models_by_owner(owner: str):
    init_bunnet(database=db_sync, document_models=[Asisstant])
    chat_models = Asisstant.find(Asisstant.owner == owner).to_list()
    return chat_models


@chat_model_router.delete("/delete/{chat_model_id}")
async def delete_chat_model(chat_model_id: str):
    init_bunnet(database=db_sync, document_models=[Asisstant])
    chat_model = Asisstant.get(chat_model_id).run()
    if not chat_model:
        raise HTTPException(status_code=404, detail="Chat model not found.")
    chat_model.delete()
    return Response(status_code=200, content="Chat model deleted successfully.")


@chat_model_router.get("/get/{chat_model_id}")
async def get_chat_model(chat_model_id: str):
    chat_model = await db_async["chat_models"].find_one(
        {"_id": ObjectId(chat_model_id)}
    )
    print(chat_model)
    if not chat_model:
        raise HTTPException(status_code=404, detail="Chat model not found.")
    return JSONResponse(
        content={
            "_id": str(chat_model.get("_id")),
            "user_id": str(chat_model.get("user_id")),
            "assistant_name": chat_model.get("asistant_name"),
            "description_assistant": chat_model.get("decription_assistant"),
            "opening_greeting": chat_model.get("opening_greeting"),
            "list_knowledge_base_id": [str(x) for x in chat_model.get("list_knowledge_base_id", [])],
            "model": chat_model.get("model"),
            "system_prompt": chat_model.get("system_prompt"),
            "max_doc": chat_model.get("max_doc"),
            "temperature": chat_model.get("temperature"),
            "top_p": chat_model.get("top_p"),
        }
    )
