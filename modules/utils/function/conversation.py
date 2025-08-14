from bson import ObjectId
from core.config import db_async


async def set_conversation_name(conversation_id):
    # Check convesation name
    conversation = await db_async["Conversation"].find_one(
        {"_id": ObjectId(conversation_id)}
    )
    if conversation["name"] is None:
        # Get first question
        first_question = await db_async["History"].find_one(
            {"conversation_id": ObjectId(conversation_id)}
        )
        if first_question:
            question = first_question["question"]
            await db_async["Conversation"].update_one(
                {"_id": ObjectId(conversation_id)}, {"$set": {"name": question}}
            )
