from datetime import datetime, timedelta
from sqlalchemy import DateTime
from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
from models.shipper import Shipper
from database.session import get_db
# from models.user import User
from models.order import Order
from models.profile import Profile
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from auth.utils import get_current_user, authenticate_user, bcrypt_context
from starlette import status
from enum import Enum
from jose import JWTError, jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from decouple import config
import random

SECRET_KEY= config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 10
MAIL_USERNAME = config("MAIL_USERNAME")
MAIL_PASSWORD = config("MAIL_PASSWORD")
MAIL_FROM = config("MAIL_FROM")

class GenderStatusEnum(str, Enum):
    Male = 'Male'
    Female = 'Female'
    NoResponse = 'Prefer not to respond'

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    dependencies=[Depends(get_current_user)]
)
router2 = APIRouter(
    prefix="/profile",
    tags=["profile"],
    dependencies=[Depends(get_current_user)]
)

public_router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)
shipper_router = APIRouter(
    prefix="/shipper",
    tags=["shipper"]
)  

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

class Address(BaseModel):
    address_number: str
    street: str
    ward: str
    district: str

class UserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CreateUserRequest(BaseModel):
    name: str
    address: Address
    phone: str
    gender: GenderStatusEnum
    age: int

class UserResponse(BaseModel): #done
    user_id: int
    name: str
    gender: GenderStatusEnum
    age: int
    phone: str
    address: str

class RegisterUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str

class UpdateProfileRequest(BaseModel):
    name: str = Field(None, max_length=50)
    gender: str = Field(None, max_length=20)
    age: int = Field(None, ge=0)
    phone: str = Field(None, max_length=15)
    address: str = Field(None, max_length=255)

# class RegisterShipperRequest(BaseModel):
#     username: str
#     email: EmailStr
#     password: str = Field(..., min_length=6)
#     confirm_password: str
#     role: int = 3

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), ):
    user = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user

@router.get("/", response_model=Dict[str, Any])
def get_paging_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):

        # Total number of users
        total_users = db.query(Profile).count()

        # Fetch paginated list of users
        users = db.query(Profile).offset((page - 1) * per_page).limit(per_page).all()

        # Format the response
        user_responses = [
            {
                "user_id": user.user_id,
                "name": user.name,
                # "email": user.email,
                "phone": user.phone,
                "address": user.address,
                # "status": user.status,
                # "Date_created": user.Date_created,
                # "role": user.role,
                #table profile trong models chưa có mấy cái xanh lá nên nếu để thì nó lỗi 500 á
            }
            for user in users
        ]

        total_pages = (total_users + per_page - 1) // per_page
        return {
            "total": total_users,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": user_responses
        }
    
# A PUT REQUEST TO UPDATE USER
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, _user: CreateUserRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    user_data = _user.model_dump(exclude_unset=True, exclude_none=True)
    user_data = _user.dict()
    
    
    address = _user.address
    address_string = f" {address.address_number}, {address.street} Street, {address.ward} Ward, District/City {address.district}"
    user_data['address'] = address_string
    user = db.query(Profile).filter(Profile.user_id == user_id).update(user_data)
    # Check if user exists
    # If not, raise an error
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.commit()
    return user

#put request to update profile user 
@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_profile(user_id: int, update_request: UpdateProfileRequest, db: Session = Depends(get_db)):
    # Retrieve the user's profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    # Update profile fields if they are provided in the request
    if update_request.name:
        profile.name = update_request.name
    if update_request.gender:
        profile.gender = update_request.gender
    if update_request.age is not None:
        profile.age = update_request.age
    if update_request.phone:
        profile.phone = update_request.phone
    if update_request.address:
        profile.address = update_request.address

    db.commit()
    db.refresh(profile)
    
    return {"message": "Profile updated successfully", "profile": profile}


