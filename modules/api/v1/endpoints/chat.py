import asyncio
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent
from bson import ObjectId
from core.config import logger, db_async, db_sync, openai_client
from utils.processor.indexer import Indexer
from fastapi import APIRouter, Form, HTTPException

chat_router = APIRouter(prefix="/Chat", tags=["Chat"])
assistant_info = None


async def generate_stream(conversation_history: list[dict], assistant_info: dict):
    try:
        query = conversation_history[-1]["content"]

        retrivaler = Indexer()
        kb_ids = [str(kb_id) for kb_id in assistant_info.get("list_knowledge_base_id")]
        print("kb_ids",kb_ids)
        context = await retrivaler.search(
            query=query,
            limit=assistant_info.get("max_doc"),
            knowledge_base_id=kb_ids,
        )
        print(context)
        template = """
        Bạn là một trợ lý học tập thân thiện và cực kỳ hiểu tâm lý sinh viên.
        Trả lời ngắn gọn, đúng trọng tâm, thân thiện, có hệ thống.
        Nếu không chắc, hãy nói: "Mình không chắc, nhưng mình sẽ cố giúp…"

        Bối cảnh:
        {context}

        Câu hỏi:
        "{question}"

        Lịch sử gần đây:
        "{history_chat}"
        """

        messages = [
            {
                "role": "system",
                "content": template.format(
                    context=context,
                    question=query,
                    history_chat=conversation_history[-2:],  # lấy 5 turn gần nhất
                ),
            }
        ]

        # gọi API stream
        stream = openai_client.responses.create(
            model=assistant_info.get("model"),
            input=messages,
            stream=True,
            temperature=assistant_info.get("temperature"),
            top_p=assistant_info.get("top_p"),
        )

        # collect full response song song
        full_response = ""

        for event in stream:
            if isinstance(event, ResponseTextDeltaEvent):
                chunk = event.delta
                full_response += chunk
                yield chunk
                await asyncio.sleep(0)  # đẩy chunk ra sớm

        # return full response cuối cùng để lưu DB
        yield f"__FULL_RESPONSE_END__{full_response}"

    except Exception as e:
        logger.error(f"❌ Lỗi khi gọi OpenAI API: {e}")
        yield f"data: {{'error': 'Lỗi khi gọi API: {str(e)}'}}\n\n"


@chat_router.post("/chat/stream")
async def chat_stream(conversation_id: str = Form(...), message: str = Form(...)):
    global assistant_info
    try:
        conversation_doc = db_sync["Conversation"].find_one(
            {"_id": ObjectId(conversation_id)}
        )
        if not conversation_doc:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # load assistant_info
        if assistant_info is None:
            assistant_info = await db_async["chat_models"].find_one(
                {"_id": ObjectId(conversation_doc.get("assistant_id"))}
            )
            if not assistant_info:
                raise HTTPException(status_code=404, detail="Assistant not found")

        # lấy history gần đây
        conversation = await (
            db_async["History"]
            .find({"conversation_id": ObjectId(conversation_id)})
            .sort("_id", 1)
            .to_list(length=None)
        )

        if len(conversation) > 3:
            conversation = conversation[-3:]

        conversation_history = []
        for history in conversation:
            messages = history.get("messages", [])
            if isinstance(messages, list):
                conversation_history.extend(messages)
            else:
                conversation_history.append(messages)

        # thêm message mới
        user_message = {"role": "user", "content": message}
        conversation_history.append(user_message)

        # tạo generator stream
        async def event_generator():
            buffer = ""
            async for chunk in generate_stream(conversation_history, assistant_info):
                if chunk.startswith("__FULL_RESPONSE_END__"):
                    # lấy full response khi stream xong
                    full_response = chunk.replace("__FULL_RESPONSE_END__", "")
                    if full_response:
                        db_sync["History"].insert_one(
                            {
                                "_id": ObjectId(),
                                "conversation_id": ObjectId(conversation_id),
                                "messages": [
                                    {"role": "user", "content": message},
                                    {"role": "assistant", "content": full_response},
                                ],
                            }
                        )
                else:
                    yield chunk

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"❌ Lỗi khi xử lý chat: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý chat: {str(e)}")
