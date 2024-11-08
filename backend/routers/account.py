from datetime import datetime, timedelta
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from database.session import get_db
from models.profile import Profile
from models.account import Account
from sqlalchemy.orm import Session
from auth.utils import get_current_user, bcrypt_context, check_admin
from starlette import status
from enum import Enum
from decouple import config
import random

class StatusEnum(str, Enum):
    Active = 'Active'
    Inactive = 'Inactive'
    Blocked = 'Blocked'

router = APIRouter(
    prefix="/account",
    tags=["account"],
    dependencies=[Depends(get_current_user)]
)

class Address(BaseModel):
    address_number: str
    street: str
    ward: str
    district: str

class CreateUserRequest(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6)

class CreateAdminRequest(BaseModel):
    email: str
    username: str
    password: str
    role: int

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    phone: str
    address: str
    status: StatusEnum
    Date_created: datetime
    role: int

class RegisterUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str

pending_users = {}

def create_access_code(data: dict, expires_delta: timedelta = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    access_code = random.randint(100000, 999999)
    
    pending_users[data["email"]] = {
        "username": data["username"],
        "password": data["password"],
        "access_code": access_code,
        "expires_at": expire
    }
    
    return access_code

@router.get("/accounts", response_model=Dict[str, Any], dependencies=[Depends(check_admin)])
def get_paging_accounts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    total_accounts = db.query(Account).count()
    accounts = (
        db.query(Account)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    account_responses = [
        {
            "user_id": account.user_id,
            "email": account.email,
            "username": account.username,
            "status": account.status,
            "date_created": account.Date_created,
            "role": account.role,
        }
        for account in accounts
    ]

    total_pages = (total_accounts + per_page - 1) // per_page
    return {
        "total": total_accounts,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": account_responses
    }

@router.post("/create_account_for_user")
async def create_account_user(account: CreateUserRequest, db: Session = Depends(get_db)):
    account.password = bcrypt_context.hash(account.password)
    check_user_email = db.query(Account).filter(Account.email == account.email).first()
    if check_user_email is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The email already exists")
    check_user_username = db.query(Account).filter(Account.username == account.username).first()
    if check_user_username is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The username already exists")
    
    new_account = Account(email=account.email, username=account.username, password=account.password)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account.user_id

@router.delete("/delete_account", dependencies=[Depends(check_admin)])
async def delete_account_user(user_id: int, db: Session = Depends(get_db)):
    acc = db.query(Account).filter(Account.user_id == user_id).first()
    if acc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no account")
    if acc.email == "admin@example.com":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete an admin account")
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no profile")
    if profile.name == "Admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete an admin profile")
    
    db.delete(acc)
    db.delete(profile)
    db.commit()
    
    return {
        "Message": "Account deleted successfully"
    }
