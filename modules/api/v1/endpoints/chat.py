import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from core.config import logger
import json
from core.config import openai_client
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from core.config import db_async, db_sync
from bson import ObjectId
from openai.types.responses import ResponseTextDeltaEvent
from utils.retrival import RetrievalPipeline
from utils.processor.indexer import Indexer
chat_router = APIRouter(prefix="/Chat", tags=["Chat"])

assistant_info = None

async def generate_stream(
    conversation_history: list[dict],
    assistant_info: dict = None,
):
    try:
        # Chuẩn bị messages
        query = conversation_history[-1]["content"]
        print("query",query)
        retrivaler = Indexer()
        context = await retrivaler.search(query=query,limit=assistant_info.get('max_doc'),knowledge_base_id = assistant_info.get('list_knowledge_base_id'))
        # print("CONTEXT",context)
        template = """
        Bạn là một trợ lý học tập thân thiện và cực kỳ hiểu tâm lý sinh viên.
        Phải trả lời ngắn gọn, đúng trọng tâm, thân thiện và có hệ thống.
        Nếu không chắc, hãy lịch sự nói: "Mình không chắc, nhưng mình sẽ cố giúp…", rồi gợi ý cách học thêm.
        Sau đây là bối cảnh:
        {context}

        Câu hỏi của bạn:
        "{question}"

        Co the xem lai lich su chat o day de lam ro ngu canh : 
        "{history_chat}"
        === Hướng dẫn cách trả lời ===
        1. Giải thích khái niệm ngắn gọn (nếu cần)  
        2. Chia nhỏ thành các bước học / suy nghĩ  
        3. Nếu có thể, đưa ví dụ hoặc analogies dễ hiểu  
        4. Cuối cùng, cung cấp tip học + gợi ý tài liệu tham khảo (nếu có)

        Đừng trả lời dài như báo cáo, nhưng cũng đừng hời hợt. Cứ như đang ngồi bắt chuyện trong buổi học thêm.
        """

        messages = [
            {"role": "system", "content": template.format(
                context=context,
                question=query , 
                history_chat = conversation_history[-1:-5]
            )}
        ]
        # messages.extend(f"co the tham khao mot so lich su chat sau de lam ro ngu canh : {conversation_history[-1:-3]}")
        print("MESSAGE:",messages)
        # Gọi streaming từ OpenAI
        stream =  openai_client.responses.create(
            model=assistant_info.get('model'),
            input=messages,
            stream=True,
            temperature=assistant_info.get('temperature'),
            top_p=assistant_info.get('top_p')
        )

        # Stream các chunk về client
        for event in stream :
            if isinstance(event,ResponseTextDeltaEvent):
                yield event.delta

        # return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"❌ Lỗi khi gọi OpenAI API: {e}")
        yield f"data: {{'error': 'Lỗi khi gọi API: {str(e)}'}}\n\n"
async def stream_response(
    conversation_history: list[dict],
    model: str = "gpt-4o-mini",
):
    return StreamingResponse(generate_stream(conversation_history, model), media_type="text/event-stream")
@chat_router.post("/chat/stream")
async def chat_stream(conversation_id: str = Form(...), message: str = Form(...)):
    global assistant_info
    try:
        conversation = (
        db_sync["Conversation"]
        .find_one({"_id": ObjectId(conversation_id)})
        )
        print(conversation)
         # Nếu chưa có thì load từ DB
        if assistant_info is None:
            assistant_info = await db_async["chat_models"].find_one(
                {"_id": ObjectId((conversation.get('aisstant_id')))}
            )
            print("assistant_info",assistant_info)
            if not assistant_info:
                raise HTTPException(status_code=404, detail="Assistant not found")
        # Lấy lịch sử chat từ MongoDB
        conversation = await db_async["History"].find({"conversation_id": ObjectId(conversation_id)}).sort("_id", 1).to_list(length=None)
        print("Full conversation:",conversation)
        # Nếu không tìm thấy conversation, tạo mới
        if not conversation:
            conversation = []
        else :
            if len(conversation) > 3 : 
                conversation = conversation[-3:]
        # Tạo conversation_history từ messages trong DB
        conversation_history = []
        for history in conversation:
            messages = history.get("messages", [])
            if isinstance(messages, list):
                conversation_history.extend(messages)  # thay vì append
            else:
                conversation_history.append(messages)
        print("conversation_history",conversation_history)
        # Thêm tin nhắn mới của người dùng
        user_message = {"role": "user", "content": message}
        conversation_history.append(user_message)
        logger.debug(f"Updated conversation_history: {conversation_history}")

        # Gọi streaming response
        model = assistant_info.get('model')
        # response = await stream_response(conversation_history, model)

        # Thu thập full response để lưu vào DB
        full_response = ""
        result = generate_stream(conversation_history, assistant_info)
        
        async for chunk in result:
            full_response += chunk
        print("FULL RESPONE",full_response)
        # Thêm response của AI vào lịch sử
        # db_sync["History"].insert_one({
        #     "_id": ObjectId(),
        #     "conversation_id": ObjectId(conversation_id),
        #     "role": "user",
        #     "content": message,
        # })
        if full_response:
            conversation_history.append({"role": "assistant", "content": full_response})
            print(conversation_history)
            # Cập nhật lịch sử chat vào MongoDB
            db_sync["History"].insert_one({
                "_id": ObjectId(),
                "conversation_id": ObjectId(conversation_id),
                "messages": [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": full_response},
                ]
            })

        return full_response

    except Exception as e:
        logger.error(f"❌ Lỗi khi xử lý chat: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý chat: {str(e)}")