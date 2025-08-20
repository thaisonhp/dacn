from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import jwt
from core.config import db_async ,db_sync
from models.user import User
from bunnet import init_bunnet

load_dotenv()

# Environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Initialize Bunnet with async database
init_bunnet(database=db_sync, document_models=[User])

auth_router_v2 = APIRouter(prefix="/auth_v2", tags=["Auth"])

# Configure OAuth
oauth = OAuth()
CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name="google",
    server_metadata_url=CONF_URL,
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)

@auth_router_v2.get("/auth/google")
async def login_via_google(request: Request):
    print(f"REDIRECT_URI used: {REDIRECT_URI}")
    if not REDIRECT_URI:
        raise HTTPException(status_code=500, detail="REDIRECT_URI not configured")
    return await oauth.google.authorize_redirect(request, REDIRECT_URI)

@auth_router_v2.get("/auth/google/callback")
async def google_callback(request: Request):
    print("Đã vào endpoint /auth/google/callback")
    try:
        # Lấy token từ Google
        token = await oauth.google.authorize_access_token(request)
        print("Token:", token)

        # Sử dụng userinfo từ token
        user_info = token.get("userinfo")
        if not user_info:
            raise HTTPException(status_code=400, detail="Không tìm thấy userinfo trong token")

        print("User info:", user_info)

        # Kiểm tra các trường bắt buộc
        required_fields = ["email", "name", "sub"]
        if not all(field in user_info for field in required_fields):
            raise HTTPException(status_code=400, detail="Thông tin người dùng không đầy đủ")

        # Tìm hoặc tạo người dùng
        user = db_sync['users'].find_one({"email": user_info["email"]})
        if not user:
            print("Tạo mới user")
            user = User(
                username=user_info["email"].split("@")[0],
                email=user_info["email"],
                full_name=user_info["name"],
                google_id=user_info["sub"],
            )
            user.insert()
        else:
            print("User đã tồn tại")

        # Tạo JWT
        payload = {
            "sub": str(user.id),
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=24),
        }
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        print("JWT:", jwt_token)

        return JSONResponse(
            content={
                "access_token": jwt_token,
                "token_type": "bearer",
                "user": user.to_dict(),
            }
        )
    except OAuthError as e:
        print(f"Lỗi OAuth: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Lỗi OAuth: {str(e)}")
    except Exception as e:
        print(f"Lỗi server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")