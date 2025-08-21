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
from fastapi.responses import JSONResponse

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
    result = send_otp_email(to_email=to_email, otp_code=otp_code)
    return JSONResponse(
        content={
            "success": True,
            "message": "OTP sent successfully",
            "result": result,
            "otp_code": otp_code
        }
    )

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
        otp_doc = await db_async["otp_codes"].find_one({"email": data.email, "otp": data.otp_code})
        if not otp_doc:
            raise HTTPException(status_code=400, detail="Sai hoặc hết hạn OTP")
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name ,
        role = data.role
    )
    user.set_password(data.password)
    user.create()
    payload = {
        "sub": str(user.id),
        "role": data.role ,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"message": "Đăng ký thành công", "user": user.to_dict(),"access_token": token}

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
        "sub": str(mongo_user_dict.get('_id')),
        "role": mongo_user_dict.get("role", "user") ,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": user.to_dict()}  

from fastapi import Body

# ------------------- Quên mật khẩu: gửi OTP -------------------
@auth_router.post("/get-otp-reset-password")
async def get_otp_reset_password(email: EmailStr = Body(..., embed=True)):
    user = await db_async["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")
    
    otp_code = generate_otp()
    await save_otp_to_db(email, otp_code)
    result = send_otp_email(to_email=email, otp_code=otp_code)

    return JSONResponse(
        content={
            "success": True,
            "message": "OTP để reset password đã được gửi qua email",
            "result": result
        }
    )


# ------------------- Reset mật khẩu -------------------
# ------------------- Validate OTP -------------------
class ValidateOTPSchema(BaseModel):
    email: EmailStr
    otp_code: str

@auth_router.post("/validate-otp")
async def validate_otp(data: ValidateOTPSchema):
    otp_doc = await db_async["otp_codes"].find_one(
        {"email": data.email, "otp": data.otp_code}
    )
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Sai hoặc hết hạn OTP")

    return {"success": True, "message": "OTP hợp lệ"}


# ------------------- Reset mật khẩu bằng old_password -------------------
class ResetPasswordSchema(BaseModel):
    email: EmailStr
    new_password: str

@auth_router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema):
    # Tìm user theo email
    mongo_user_dict = await db_async["users"].find_one({"email": data.email})
    if not mongo_user_dict:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")

    # Check old_password
    user = User(
        username=mongo_user_dict.get("username"),
        email=mongo_user_dict.get("email"),
        full_name=mongo_user_dict.get("full_name"),
        password_hash=mongo_user_dict.get("password_hash"),
        avatar_url=mongo_user_dict.get("avatar_url"),
        role=mongo_user_dict.get("role", "user"),
        is_verified=mongo_user_dict.get("is_verified", False),
        google_id=mongo_user_dict.get("google_id"),
        created_at=mongo_user_dict.get("created_at"),
        updated_at=datetime.utcnow(),
    )
    # Update password
    user.set_password(data.new_password)
    await db_async["users"].update_one(
        {"email": data.email},
        {"$set": {"password_hash": user.password_hash, "updated_at": datetime.utcnow()}}
    )

    return {"success": True, "message": "Mật khẩu đã được cập nhật thành công"}
