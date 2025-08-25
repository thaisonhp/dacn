from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime
from bson import ObjectId
from bunnet import init_bunnet, Document
from pydantic import BaseModel
from core.config import db_sync, db_async
from core.security import get_current_user_id
from models.user import User
from schema.user import UserCreate , UserOut , UserUpdate




# ---- Initialize Bunnet ----
init_bunnet(database=db_sync, document_models=[User])

# ---- Router setup ----
user_router = APIRouter(prefix="/users", tags=["Users"])

# --- Create user ---
@user_router.post("/", response_model=UserOut)
async def create_user(data: UserCreate, user_id: str = Depends(get_current_user_id)):
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        avatar_url=data.avatar_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    new_user.insert()
    return UserOut(
        id=str(new_user.id),
        full_name=new_user.full_name,
        email=new_user.email,
        avatar_url=new_user.avatar_url,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )

# --- Read all users ---
@user_router.get("/", response_model=List[UserOut])
async def list_users():
    docs = User.find().to_list()
    return [
        UserOut(
            id=str(doc.id),
            username=doc.username,
            full_name=doc.full_name,
            email=doc.email,
            role=doc.role,
            avatar_url=doc.avatar_url,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in docs
    ]

# --- Get single user ---
@user_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    doc = User.get(user_id).run()
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
            id=str(doc.id),
            username=doc.username,
            full_name=doc.full_name,
            email=doc.email,
            role=doc.role,
            avatar_url=doc.avatar_url,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

# --- Update user ---
@user_router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, data: UserUpdate):
    doc = User.get(user_id).run()
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    doc.set(update_data)
    doc.save()
    UserOut(
            id=str(doc.id),
            username=doc.username,
            full_name=doc.full_name,
            email=doc.email,
            role=doc.role,
            avatar_url=doc.avatar_url,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

# --- Delete user ---
@user_router.delete("/{user_id}")
async def delete_user(user_id: str):
    doc = User.get(user_id).run()
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    doc.delete()
    return JSONResponse(content={"ok": True, "message": "User deleted"})

