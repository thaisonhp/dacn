import base64
import json
from typing import Annotated, Any, Dict, Optional

import httpx
from bson import ObjectId
from core.config import MediaType, db_async, linkType, settings
from core.security import get_current_user, get_current_user_websocket
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from loguru import logger

from utils.function.mime_type import process_file
from utils.llm import build_response


# ---------------------------------------------
chat_router = APIRouter(prefix="/chat", tags=["Chat"])


# region Chat
@chat_router.post("")
async def chat(
    information: Annotated[str, Depends(get_current_user)],
    request: Request,
    conversation_id: str = Form(...),
    messages: str = Form(default=None),
    stream: bool = Form(...),
    files: list[UploadFile] | None = None,
    link: str | None = Form(default=None),
    # client_info: Dict[str, Any] = Depends(get_client_info_dependency),
):
    # region Validate Request
    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    if not conversation_id:
        raise HTTPException(status_code=400, detail="No conversation ID provided")

    chat_model_id = information.get("chatbotModelId")
    request_type = information.get("type", "production")

    if not chat_model_id:
        raise HTTPException(status_code=400, detail="No chat model ID provided")

    # Get allow domain
    # allow_domain_documents = (
    #     await client_motor["core_admin"]["chatbot_domains"]
    #     .find({"chatbotId": ObjectId(chat_model_id)})
    #     .to_list()
    # )
    # allow_domain = [f"https://{domain['domain']}" for domain in allow_domain_documents]
    # allow_domain.extend(settings.DOMAIN_PREVIEW)
    # if (
    #     request.headers.get("origin")
    #     and request.headers.get("origin") not in allow_domain
    # ):
    #     raise HTTPException(status_code=403, detail="Domain not allowed")

    # Process images if provided
    file_paths = []
    context_files = ""
    if files:
        for file in files:
            object_name = f"conversation/{conversation_id}/{file.filename}"
            file_url = f"https://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"
            data = await file.read()
            media_type = await process_file(
                content=data, object_name=object_name, content_type=file.content_type
            )

            # Image processing
            if media_type == MediaType.image.name:
                file_paths.append(
                    {
                        "type": MediaType.image.name,
                        "url": file_url,
                        "file_name": file.filename,
                    }
                )
            # Pdf processing
            else:
                context_files = base64.b64encode(data).decode("utf-8")
                file_paths.append(
                    {
                        "file_name": file.filename,
                        "context": context_files,
                        "type": MediaType.document.name,
                    }
                )
    chat_model = await db_async["chat_models"].find_one(
        {"_id": ObjectId(chat_model_id)}
    )
    if chat_model:
        vector_store_id = chat_model.get("vector_store_id", [])
        library_id = chat_model.get("library_id", [])
        mcp_server = chat_model.get("mcp_server", False)
        system_prompt = chat_model.get("prompt", None)
        qa_index = chat_model.get("qa", [])
        model = chat_model.get("model", "gpt-4o-mini")
        temperature = chat_model.get("temperature", 0.2)
        max_doc = chat_model.get("max_doc", 20)
        result = await build_response(
            user_prompt=messages,
            system_prompt=system_prompt,
            vector_store_id=vector_store_id,
            library_id=library_id,
            mcp_server=mcp_server,
            qa_index=qa_index,
            conversation_id=conversation_id,
            model=model,
            stream=stream,
            db=db_async,
            files=file_paths,
            request_type=request_type,
            temperature=temperature,
            max_doc=max_doc,
            chat_model_id=chat_model_id,
            # client_info=client_info,
        )
        return result
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Chat model with id '{chat_model_id}' not found in the database.",
        )


