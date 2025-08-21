from fastapi import FastAPI

# The file where HybridSearcher is stored

from fastapi import APIRouter, Depends,File, Form, HTTPException, UploadFile ,Query
from typing import List
from utils.retrival import RetrievalPipeline
from core.config import settings
from pathlib import Path

search_router = APIRouter(prefix="/retrieval", tags=["Retrieval"])

# Create a neural searcher instance
retrivaler = RetrievalPipeline()


@search_router.get("/api/search")
async def search_startup(query: str, limit : int ,knowledge_base_id : List[str] = Query(...)):
    return await retrivaler.retrieval(query=query , limit=limit,knowledge_base_id=knowledge_base_id)


