import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.session import get_db
from models.user import Account, Role, Profile
from sqlalchemy.orm import Session
from typing import Optional
from auth.utils import get_current_user, authenticate_user, bcrypt_context
from starlette import status

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(get_current_user)]
)

class Role(BaseModel):
    role_id: uuid.uuid4
    name_role: str

class UserRequest(BaseModel):
    user_id: uuid.uuid4
    username: str
    password: str
    email: str
    role: Role

#cho phép tạo mà k cần nhập profile
    
class CreateUserRequest(BaseModel):
    # user_id: str 
    email: str
    username: str
    name: str
    address: str
    phone: str
    password: str

class UserResponse(BaseModel):
    user_id: str 
    username: str
    password: str
    email: str
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
