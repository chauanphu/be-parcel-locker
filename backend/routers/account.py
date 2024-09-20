from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
# from models.shipper import Shipper
# from models.order import Order
from database.session import get_db
from models.profile import Profile
from models.account import Account
from sqlalchemy.orm import Session
from auth.utils import get_current_user, authenticate_user, bcrypt_context
from starlette import status
from enum import Enum
from jose import JWTError, jwt
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
router2 = APIRouter( 
    prefix="/account",
    tags=["account"],
    dependencies=[Depends(get_current_user)]
)
public_router = APIRouter(
    prefix="/account",
    tags=["account"]
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


class CreateUserRequest(BaseModel):
    email: str
    username: str
    password: str

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

# class RegisterShipperRequest(BaseModel):
#     username: str
#     email: EmailStr
#     password: str = Field(..., min_length=6)
#     confirm_password: str
#     role: int = 3



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


#to create a new account
#@router.push()

@router.post("/create_account_for_admin")
async def create_account_admin(account: CreateAdminRequest, db: Session = Depends(get_db)):
    account.password = bcrypt_context.hash(account.password)
    account.role = 1
    new_account = Account(**account.model_dump())
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account.user_id

@router.post("/create_account_for_user")
async def create_account_user(account: CreateUserRequest, db: Session = Depends(get_db)):
    account.password = bcrypt_context.hash(account.password)
    new_account = Account(**account.model_dump())
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account.user_id

@router.delete("/delete_account_for_current_user")
async def delete_account_user(db: Session = Depends(get_db),
                              current_user: Account = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.user_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no profile")
    if profile.name == "Admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete an admin profile")
    acc = db.query(Account).filter(Account.user_id == current_user.user_id).first()
    if acc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is no account")
    if acc.email == "admin@example.com":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete an admin account")
    
    db.delete(profile)
    db.commit()
    db.delete(acc)
    db.commit()
    
    return {
        "Message": "Account deleted sucessfully"
    }
    