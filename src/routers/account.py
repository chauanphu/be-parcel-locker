from datetime import datetime, timedelta
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from database.session import get_db
from models.profile import Profile
from models.account import Account
from sqlalchemy.orm import Session
from auth.utils import get_current_user, check_admin, hash_password
from starlette import status
from enum import Enum
from decouple import config
import random

SECRET_KEY= config("SECRET_KEY")
ALGORITHM = config("algorithm", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 10

class StatusEnum(str, Enum):
    Active = 'Active'
    Inactive = 'Inactive'
    Blocked = 'Blocked'

router = APIRouter(
    prefix="/account",
    tags=["account"],
    dependencies=[Depends(get_current_user)]
)

class AddressModel(BaseModel):
    address_number: str
    street: str
    ward: str
    district: str


class CreateUserRequestModel(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=6)


class CreateAdminRequestModel(BaseModel):
    email: str
    username: str
    password: str
    role: int

class UserResponseModel(BaseModel):
    user_id: int
    name: str
    email: str
    phone: str
    address: str
    status: StatusEnum
    date_created: datetime
    role: int
class RegisterUserRequestModel(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str




def create_access_code(data: dict, expires_delta: timedelta = None):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    access_code = random.randint(100000, 999999)
    
    # Store the access code and expiration time
    pending_users[data["email"]] = {
        "username": data["username"],
        "password": data["password"],
        "access_code": access_code,
        "expires_at": expire
    }
    
    return access_code


pending_users = {} # For pending users


#This doesn't need right now 

# @public_router.post('/Register_by_code', status_code=status.HTTP_201_CREATED)
# async def register_user(register_user_request: RegisterUserRequest, db: Session = Depends(get_db)):
#     if register_user_request.password != register_user_request.confirm_password:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail='Confirm password not like password')
    
#     user = authenticate_user(register_user_request.username, register_user_request.password, db)
#     if user:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail='Email already exists')
    
#     if register_user_request.username == Account.username:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail='User already exists')
        
#     token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_code = create_access_code(
#         data={"email": register_user_request.email, "username": register_user_request.username, "password": bcrypt_context.hash(register_user_request.password)}, 
#         expires_delta=token_expires
#     )
    
#     message = MessageSchema(
#         subject="Email Confirmation",
#         recipients=[register_user_request.email],
#         body=f"Your confirmation code is: {access_code}",
#         subtype="html"
#     )
    
#     fm = FastMail(conf)
#     await fm.send_message(message)
    
#     return {"message": "Please check your email for the confirmation code"}




# @public_router.post("/confirm_code", status_code=status.HTTP_201_CREATED)
# async def confirm_email(code: int, email: str, db: Session = Depends(get_db)):
#     user_data = pending_users.get(email)
#     if user_data is None:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    
#     if user_data["access_code"] != code:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    
#     if datetime.utcnow() > user_data["expires_at"]:
#         pending_users.pop(email)
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired code")
    
#     new_user = Account(email=email, username=user_data["username"], password=user_data["password"])
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
    
#     new_profile = Profile(
#         user_id=new_user.user_id,
#         name = 'null',
#         gender = 'Male',
#         age = 0,
#         phone = 0,
#         address = 'null'
#         )
#     db.add(new_profile)
#     db.commit()
#     pending_users.pop(email)
    
#     return {"message": "Email confirmed and user registered successfully"}


@router.get(
    "/",
    response_model=Dict[str, Any],
    dependencies=[Depends(check_admin)]
)
async def get_accounts_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    """
    Get paginated list of accounts.
    
    Args:
        page: Page number (starts from 1)
        per_page: Number of items per page
        
    Returns:
        Paginated list of accounts with total count and page information
    """
    # Total number of accounts
    total_accounts = db.query(Account).count()

    # Fetch paginated list of accounts
    accounts = (
        db.query(Account)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Format the response
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
    
    Args:
        account: User account creation details
        
    Returns:
        Newly created user ID
        
    Raises:
        HTTPException: If email or username already exists
    """
    account.password = hash_password(account.password)
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

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin)]
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
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no profile")
    if profile.name == "Admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete an admin profile")
    
    db.delete(acc)
    db.delete(profile)
    db.commit()
    
    
    return {
        "Message": "Account deleted sucessfully"
    }
