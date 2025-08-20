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
# -------------------------------------------------
chat_model_router = APIRouter(prefix="/chat-model", tags=["Chat Model"])


@chat_model_router.post("/create")
async def create_chat_model(data: CreateAsisstant, background_tasks: BackgroundTasks ,user_id : str = Depends(get_current_user_id) ):
    init_bunnet(database=db_sync, document_models=[Asisstant])
    id = str(ObjectId())
    chat_model = Asisstant(
        user_id=user_id,
        asistant_name=data.name,
        decription_assistant =data.description_assistant,
        opening_greeting=data.opening_greeting,
        list_knowledge_base_id=data.list_knowledge_base_id,
        model=data.model,
        system_prompt =data.prompt,
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
    chat_model.pop("_id", None)
    chat_model.pop("createdAt", None)
    chat_model.pop("updatedAt", None)

    if not chat_model:
        raise HTTPException(status_code=404, detail="Chat model not found.")
    return chat_model
