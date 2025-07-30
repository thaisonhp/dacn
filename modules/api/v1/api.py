from fastapi import APIRouter

from api.v1.endpoints.indexing import index_router
from api.v1.endpoints.search import search_router

# --------------------------------------
api_v1 = APIRouter()

api_v1.include_router(index_router)
api_v1.include_router(search_router)
