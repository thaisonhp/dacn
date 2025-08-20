import warnings

import uvicorn
from api.api import api_v1
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from api.v2.endpoints.auth import auth_router_v2  # Điều chỉnh đường dẫn theo dự án của bạn
# from fastapi_pagination import add_pagination
import os 
from dotenv import load_dotenv
load_dotenv()
# ----------------------------------------------------------------
warnings.filterwarnings("ignore")

from starlette.middleware.sessions import SessionMiddleware

api = FastAPI(
    title="Student Asisstant", description="Student Asisstant BACKEND", version="1.0.0", root_path="/api/v2"
)
api.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),  # Dùng cùng SECRET_KEY từ .env
    session_cookie="session",
    max_age=3600,  # Session hết hạn sau 1 giờ
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
api.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "super-secret"))


@api.get("/")
async def root():
    return {"message": "Welcome to XBOT Backend V2!"}


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8053, workers=1) 