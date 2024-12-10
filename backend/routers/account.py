from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from database.session import get_db
from models.account import Account
from sqlalchemy.orm import Session
from auth.utils import get_current_user, check_admin, hash_password
from starlette import status
from enum import Enum
from decouple import config
import random

from models.role import Role

SECRET_KEY= config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 10

router = APIRouter(
    prefix="/account",
    tags=["account"]
)

class AddressModel(BaseModel):
    address_number: str
    street: str
    ward: str
    district: str

class RoleEnum(Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    SHIPPER = "shipper"

class CreateUserRequestModel(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6)
    name: str
    phone: str
    address: str
    age: int
    role: Optional[RoleEnum] = RoleEnum.CUSTOMER

class CreateAdminRequestModel(BaseModel):
    email: str
    username: str
    password: str
    role: int

class RoleResponseModel(BaseModel):
    role_id: int
    name: str

class GenderEnum(str, Enum):
    MALE = 'Male'
    FEMALE = 'Female'
    PREFER_NOT_TO_RESPOND = 'Prefer not to respond'

class UserResponseModel(BaseModel):
    user_id: int
    email: str
    phone: str
    username: str
    name: str
    gender: GenderEnum
    age: int
    address: str
    role: RoleResponseModel

class RegisterUserRequestModel(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str

class PaginatedResponseModel(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    data: list[UserResponseModel]

@router.get(
    "/",
    response_model=PaginatedResponseModel,
    dependencies=[Depends(check_admin), Depends(get_current_user)]
)
async def get_accounts_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    """
    Get paginated list of accounts.
    """
    total_accounts = db.query(Account).count()

    accounts = (
        db.query(Account)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    account_responses = [
        UserResponseModel(
            user_id=account.user_id,
            email=account.email, 
            phone=account.phone,
            username=account.username,
            name=account.name if account.name is not None else "",
            gender=account.gender,
            age=account.age,
            address=account.address,
            role=RoleResponseModel(
                role_id=account.role,
                name=account.role_rel.name
            )
        ) for account in accounts
    ]

    total_pages = (total_accounts + per_page - 1) // per_page
    
    return PaginatedResponseModel(
        total=total_accounts,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        data=account_responses
    )

@router.get(
    "/me",
    dependencies=[Depends(get_current_user)]
)
async def get_current_user_account(
    current_user: Account = Depends(get_current_user)
):
    """
    Get the current user account.
    """
    return UserResponseModel(
        user_id=current_user.user_id,
        email=current_user.email, 
        phone=current_user.phone,
        username=current_user.username,
        name=current_user.name if current_user.name is not None else "",
        gender=current_user.gender,
        age=current_user.age,
        address=current_user.address,
        role=RoleResponseModel(
            role_id=current_user.role,
            name=current_user.role_rel.name
        )
    )

@router.post(
    "/",
    response_model=int,
    status_code=status.HTTP_201_CREATED
)
async def create_user_account(
    account: CreateUserRequestModel,
    db: Session = Depends(get_db)
):
    """
    Create a new user account.

    Raises:
        HTTPException: If email or username already exists
    """
    try:
        account.password = hash_password(account.password)
        check_user_email = db.query(Account).filter(Account.email == account.email).first()
        role = db.query(Role).filter(Role.name == account.role.value).first()
        if role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role does not exist")
        if check_user_email is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The email already exists")
        check_user_username = db.query(Account).filter(Account.username == account.username).first()
        if check_user_username is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The username already exists")
       
        new_account = Account(
            email=account.email,
            username=account.username,
            password=account.password,
            name=account.name,
            phone=account.phone,
            address=account.address,
            age=account.age,
            role=role.role_id
        )
        db.add(new_account)
        db.commit()
        db.refresh(new_account)
        return new_account.user_id
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the account"
        )

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin), Depends(get_current_user)]
)
async def delete_user_account(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user account and associated profile.
    
    Args:
        user_id: ID of the user to delete
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If account doesn't exist or is an admin account
    """
    acc = db.query(Account).filter(Account.user_id == user_id).first()
    if acc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no account")
    if acc.email == "admin@example.com":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete an admin account")
    
    db.delete(acc)
    db.commit()
    
    return {
        "Message": "Account deleted sucessfully"
    }
