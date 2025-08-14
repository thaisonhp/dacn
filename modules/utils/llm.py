import asyncio, json, re
from datetime import datetime
from typing import Literal
from bson import ObjectId
from bunnet import init_bunnet
from fastapi import HTTPException
from loguru import logger
from starlette.responses import StreamingResponse

from core.config import ChatStep, MediaType, client_motor, db_async, db_sync, settings
from models.history import History
from openai import AsyncOpenAI
from utils.function.conversation import set_conversation_name
from utils.function.regex import regex_ciatation

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def log_conversation(**kwargs):
    await init_bunnet(database=db_sync, document_models=[History])
    await History(**kwargs).insert()


async def extract_message_output(response, annotations: list):
    msg_output = next((o for o in response.output if o.type == "message"), None)
    if not msg_output: return "", []
    content = next((c for c in msg_output.content if c.type == "output_text"), None)
    if not content: return "", []

    file_ids = [a.file_id for a in content.annotations if hasattr(a, "file_id")]
    chunks = await client_motor[settings.ADMIN_DB]["text_segments"].find(
        {"openai_file_id": {"$in": file_ids}}
    ).to_list(None)

    unique_chunks, seen = [], set()
    for doc in chunks + annotations:
        name = doc.get("origin_name")
        if name and name not in seen:
            seen.add(name)
            unique_chunks.append({
                "documentId": doc.get("documentId"),
                "origin_url": doc.get("origin_url"),
                "origin_name": f"{name} (trang {doc.get('page_number', 1)})",
                "page_number": doc.get("page_number", 1)
            })
    return content.text, unique_chunks

async def build_response(user_prompt, system_prompt, vector_store_id, library_id, 
                         mcp_server, qa_index, conversation_id, model, stream, db, files, 
                         request_type, temperature, max_doc, chat_model_id=None):
    try:
        conv = await db["Conversation"].find_one({"_id": ObjectId(conversation_id)})
        prev_id = conv.get("openai_conversation_id")
        now = datetime.now().timestamp()
        qid = str(ObjectId())
        messages, refer_list = [], []

        # Xử lý file input
        if files:
            content = []
            for f in files:
                if f["type"] == MediaType.image.name:
                    content.append({"type": "input_image", "image_url": f["url"]})
                elif f["type"] == MediaType.document.name:
                    content.append({
                        "type": "input_file",
                        "filename": f["file_name"],
                        "file_data": f"data:application/pdf;base64,{f['context']}",
                    })
            if user_prompt: content.append({"type": "input_text", "text": user_prompt})
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": f"Câu hỏi: {user_prompt}"})
        
        # Call OpenAI API
        try:
            response = await client.responses.create(
                model=model,
                instructions=f"Thời gian hiện tại: {datetime.now():%Y-%m-%d}\n\n{system_prompt}\n\n{settings.ADD_PROMPT}",
                previous_response_id=prev_id,
                input=messages,
                stream=stream,
                temperature=temperature
            )
        except:
            response = await client.responses.create(
                model=model,
                instructions=f"Thời gian hiện tại: {datetime.now():%Y-%m-%d}\n\n{system_prompt}\n\n{settings.ADD_PROMPT}",
                input=messages,
                stream=stream,
                temperature=temperature
            )

        if stream:
            async def stream_gen():
                full_output = ""
                async for chunk in response:
                    if chunk.type == "response.output_text.delta":
                        regex_status, text = regex_ciatation(chunk.delta)
                        if regex_status:
                            ref = await client_motor["core_admin"]["text_segments"].find_one(
                                {"file_name_openai": text}
                            )
                            if ref: refer_list.append(ref)
                            chunk.delta = ""
                        else:
                            chunk.delta = re.sub(r"【[^】]*】", "", chunk.delta)
                            full_output += chunk.delta
                        yield json.dumps({"step": ChatStep.text.name, "content": chunk.delta}, ensure_ascii=False)
                    elif chunk.type == "response.completed":
                        full_output, annotations = await extract_message_output(chunk.response, refer_list)
                        yield json.dumps({"step": ChatStep.refer.name, "content": annotations}, ensure_ascii=False)
            return StreamingResponse(stream_gen(), media_type="text/event-stream")

        else:
            text, annotations = await extract_message_output(response, refer_list)
            text = re.sub(r"【[^】]*】", "", text)
            if not text: raise HTTPException(500, "No message output")
            return {"text": text, "refer": annotations}

    except Exception as e:
        logger.error(f"Error in build_response: {e}")
        raise HTTPException(500, f"Error: {e}")
