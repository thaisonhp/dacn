from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel, EmailStr
from models.user import User
import jwt
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
from core.config import db_sync , db_async
from utils.auth.send_mail import send_otp_email , generate_otp ,save_otp_to_db
from schema.auth import LoginSchema , SignupSchema

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
from bunnet import init_bunnet

init_bunnet(
    database=db_sync,
    document_models=[User],  # hoặc list tất cả models
    )
# ------------------- Schemas -------------------

OTP_CODE = None
@auth_router.post("/send_otp")
async def send_otp(to_email: str):
    otp_code = generate_otp()
    await save_otp_to_db(to_email, otp_code)
    result = await send_otp_email(to_email=to_email, otp_code=otp_code)
    return result

# ------------------- Signup -------------------
@auth_router.post("/signup")
async def signup(data: SignupSchema):
    # check username/email có tồn tại chưa
    if data.email is None: 
        raise HTTPException(status_code=400, detail="Thiếu Email")
    if data.otp_code is None : 
        raise HTTPException(status_code=400, detail="Thiếu OTP CODE")
    
    existing_user = await db_async["users"].find_one(
    {"$or": [{"username": data.username}, {"email": data.email}]}
)
    print(existing_user)
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Username hoặc email đã tồn tại")
    
    
    else : 
        print(OTP_CODE)
        if data.otp_code == OTP_CODE :
            pass
        else:
            raise HTTPException(status_code=400, detail="Sai otp code kiem tra email")
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name ,
        role = data.role
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
    if mongo_user_dict is None:
        raise HTTPException(status_code=400, detail="Tài khoản không tồn tại")
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
    

    if not user.check_password(data.password):
        raise HTTPException(status_code=400, detail="Mật khẩu không đúng")

    # tạo token JWT
    payload = {
        "sub": str(user.id),
        "role": mongo_user_dict.get("role", "user") ,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": user.to_dict()}  