from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
from database.session import get_db
from models.profile import Profile
from models.account import Account
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from auth.utils import get_current_user,check_admin
from starlette import status
from enum import Enum
from decouple import config

SECRET_KEY= config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 10

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
# shipper_router = APIRouter(
#     prefix="/shipper",
#     tags=["shipper"]
# )  

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
    address: str
    phone: str
    gender: GenderStatusEnum
    age: int

class UserResponse(BaseModel):
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
    gender: str = Field('Prefer not to respond', max_length=50)
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
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user

@router.get("/", response_model=Dict[str, Any], dependencies=[Depends(check_admin)])
def get_paging_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):

        # Total number of users
        total_users = db.query(Profile).count()

        # Fetch paginated list of users
        users = (
        db.query(Profile, Account)
        .join(Account, Profile.user_id == Account.user_id)  # Adjust field names accordingly
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
        # Format the response
        user_responses = [
            {
                "user_id": user.Profile.user_id,
                "name": user.Profile.name,
                "email": user.Account.email,
                "phone": user.Profile.phone,
                "address": user.Profile.address,
                "status": user.Account.status,
                "Date_created": user.Account.Date_created,
                #"role": user.role,
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

# Create user profile
@router.post("/{user_id}/create_profile")
async def create_profile(user_id: int, _user: CreateUserRequest, db: Session = Depends(get_db)):
    user = db.query(Account).filter(Account.user_id == user_id).first()
    if user == None:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile is not None:
        raise HTTPException(status_code=404, detail="Already has profile, please change to update profile")
    
    
    new_account = Profile(
        user_id=user_id,
        name=_user.name,
        address=_user.address,
        phone=_user.phone,
        gender=_user.gender,
        age=_user.age
        )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {"message": "Profile created successfully"}
    
# A PUT REQUEST TO UPDATE USER
@router.put("/{user_id}/update_profile")
def update_user(user_id: int, _user: CreateUserRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    user_data = _user.model_dump(exclude_unset=True, exclude_none=True)
    user_data = _user.dict()
    
    address = _user.address
    address_string = f" {address.address_number}, {address.street} Street, {address.ward} Ward, District/City {address.district}"
    user_data['address'] = address_string
    user = db.query(Account).filter(Account.user_id == user_id).first()
    profile = db.query(Profile).filter(Profile.user_id == user.user_id).update(user_data)    
    # Check if user exists
    # If not, raise an error
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.commit()
    return {"message": "Profile updated successfully",
            "user_id": user.username}

