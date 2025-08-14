from fastapi import APIRouter

from api.v1.endpoints.indexing import index_router
from api.v1.endpoints.search import search_router
from api.v1.endpoints.manage_conservation import conversation_router
from api.v1.endpoints.manage_chatmodel import chat_model_router
from api.v1.endpoints.chat import chat_router
from api.v1.endpoints.auth import auth_router
from api.v2.endpoints.auth import auth_router_v2
# --------------------------------------
api_v1 = APIRouter()

api_v1.include_router(index_router)
api_v1.include_router(search_router)
api_v1.include_router(conversation_router)
api_v1.include_router(chat_model_router)
api_v1.include_router(chat_router)
api_v1.include_router(auth_router)
api_v1.include_router(auth_router_v2)
