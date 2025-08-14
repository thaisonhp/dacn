from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel, EmailStr
from models.user import User
import jwt
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
from core.config import db_sync , db_async
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
from bunnet import init_bunnet

init_bunnet(
    database=db_sync,
    document_models=[User],  # hoặc list tất cả models
    )
# ------------------- Schemas -------------------
class SignupSchema(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    password: str

class LoginSchema(BaseModel):
    username_or_email: str
    password: str

# ------------------- Signup -------------------
@auth_router.post("/signup")
async def signup(data: SignupSchema):
    # check username/email có tồn tại chưa
    existing_user = await db_async["users"].find_one(
    {"$or": [{"username": data.username}, {"email": data.email}]}
)
    print(existing_user)
    if existing_user is None:
        raise HTTPException(status_code=400, detail="Username hoặc email đã tồn tại")
        
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name
    )
    user.set_password(data.password)
    user.create()
    return {"message": "Đăng ký thành công", "user": user.to_dict()}

# ------------------- Login -------------------
@auth_router.post("/login")
async def login(data: LoginSchema):
    print(f"Input username_or_email: '{data.username_or_email}'")
    mongo_user_dict = await db_async["users"].find_one(
    {"$or": [{"username": data.username_or_email}, {"email": data.username_or_email}]})
    # user = User.find_one(
    #     {"$or": [{"username": data.username_or_email}, {"email": data.username_or_email}]}
    # )
    user = User(
        username=mongo_user_dict.get("username"),
        email=mongo_user_dict.get("email"),
        full_name=mongo_user_dict.get("full_name"),
        password_hash=mongo_user_dict.get("password_hash"),  # nếu có
        avatar_url=mongo_user_dict.get("avatar_url"),
        role=mongo_user_dict.get("role", "user"),
        is_verified=mongo_user_dict.get("is_verified", False),
        google_id=mongo_user_dict.get("google_id"),
        created_at=mongo_user_dict.get("created_at"),
        updated_at=mongo_user_dict.get("updated_at")
    )
    if user is None:
        raise HTTPException(status_code=400, detail="Tài khoản không tồn tại")

    if not user.check_password(data.password):
        raise HTTPException(status_code=400, detail="Mật khẩu không đúng")

    # tạo token JWT
    payload = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": user.to_dict()}
