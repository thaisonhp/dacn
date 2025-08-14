from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os
from dotenv import load_dotenv
from core.config import db_async
from models.user import User
load_dotenv()

auth_router_v2 = APIRouter(prefix="/auth_v2", tags=["Auth"])
oauth = OAuth()

CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={'scope': 'openid email profile'},
)

@auth_router_v2.get("/auth/google")
async def login_via_google(request: Request):
    redirect_uri = os.getenv("REDIRECT_URI")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@auth_router_v2.get("/auth/google/callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)
    
    # user_info có dạng: {'email': ..., 'name': ..., 'sub': ...}
    existing_user = await db_async["users"].find_one({"email": user_info['email']})
    if not existing_user:
        print("Tao moi user")
        # tạo user mới nếu chưa có
        user = User(
            username=user_info['email'].split("@")[0],
            email=user_info['email'],
            full_name=user_info['name'],
            google_id=user_info['sub']
        )
        user.create()
     
    else:
        user = User(**existing_user)

    # có thể tạo JWT như login bình thường
    return RedirectResponse(url="http://localhost:8053/api/v2/auth_v2/auth/google")
