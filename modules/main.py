import warnings

import uvicorn
from api.v1.api import api_v1
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
# from fastapi_pagination import add_pagination

# ----------------------------------------------------------------
warnings.filterwarnings("ignore")


api = FastAPI(
    title="Qdrant_search", description="Qdrant_search BACKEND", version="1.0.0", root_path="/api/v2"
)
# add_pagination(api)
# ----------------------------------------------------------------
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api.include_router(api_v1)
api.add_middleware(GZipMiddleware, minimum_size=5000, compresslevel=3)


@api.get("/")
async def root():
    return {"message": "Welcome to XBOT Backend V2!"}


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8053, workers=1) 