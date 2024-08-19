from datetime import datetime, timedelta
from sqlalchemy import DateTime
from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
from models.shipper import Shipper
from database.session import get_db
# from models.user import User
from models.order import Order
from models.profile import Profile
from models.account import Account
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


class CreateUserRequest(BaseModel):
    email: str
    username: str
    name: str
    address: Address
    phone: str
    password: str

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

class RegisterShipperRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str
    role: int = 3


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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


@shipper_router.post('/create_shipper', status_code=status.HTTP_201_CREATED)
async def create_shipper(create_shipper_request: RegisterShipperRequest, db: Session = Depends(get_db)):
    # Check if passwords match
    if create_shipper_request.password != create_shipper_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
    
    # Check if the username or email already exists
    existing_user = db.query(Account).filter(
        (Account.username == create_shipper_request.username) #thêm email vào models shipper??
        (Account.email == create_shipper_request.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username or email already exists')
    
    # Hash the password
    hashed_password = bcrypt_context.hash(create_shipper_request.password)
    
    # Create new account with role = 3 (Shipper)
    new_account = Account(
        email=create_shipper_request.email,
        name=create_shipper_request.username,
        password=hashed_password,
        role=3  # Role for Shipper
    )
    
    # Add the new account to the database
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return {"message": "Shipper account created successfully", 
            "shipper_id": new_account.user_id,
            "role": new_account.role}


# # A POST REQUEST TO CREATE USER
# @router.post('/', status_code=status.HTTP_201_CREATED)
# async def create_user(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
#     user = authenticate_user(create_user_request.email, create_user_request.password, db)
#     if user:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail='Email already exists')
#     create_user_request.password = bcrypt_context.hash(create_user_request.password)
    
    
#     user_data = create_user_request.dict()
    
    
#     address = create_user_request.address
#     address_string = f" {address.address_number}, {address.street} Street, {address.ward} Ward, District/City {address.district}"
#     user_data['address'] = address_string
#     db_user = Account(**user_data)
    
#     print(db_user)
#     db.add(db_user)
#     db.commit()
#     return {"messsage": "User created successfully"}

pending_users = {} # For pending users


@public_router.post('/Register_by_token', status_code=status.HTTP_201_CREATED)
async def register_user(register_user_request: RegisterUserRequest, db: Session = Depends(get_db)):
    if register_user_request.password != register_user_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Confirm password not like password')
        
    user = authenticate_user(register_user_request.username, register_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User already exists')
    if register_user_request.username == Account.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User already exists')
        
        
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": register_user_request.email}, expires_delta=token_expires
    )
    
    confirmation_link = f"http://localhost:8000/confirm?token={access_token} "
    message = MessageSchema(
        subject="Email Confirmation",
        recipients=[register_user_request.email],
        body=f"""
        <h1>Welcome to Our Service</h1>
        <p>Hi {register_user_request.username},</p>
        <p>Thank you for registering with us. Please confirm your email address by clicking the link below:</p>
        <a href="{confirmation_link}">Confirm Email Address</a>
        <p>If you did not register for our service, please ignore this email.</p>
        <p>Best regards.</p>
        """,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    
    pending_users[register_user_request.email] = {
        "username": register_user_request.username,
        "password": bcrypt_context.hash(register_user_request.password)
    }
    
    return {"message": "Please check your email to confirm your registration"}


@public_router.post("/confirm",status_code=status.HTTP_201_CREATED)
async def confirm_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    
    user_data = pending_users.pop(email, None)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    new_user = Account(email=email, username=user_data["username"], password=user_data["password"])
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "Email confirmed and user registered successfully"}


@public_router.post('/Register_by_code', status_code=status.HTTP_201_CREATED)
async def register_user(register_user_request: RegisterUserRequest, db: Session = Depends(get_db)):
    if register_user_request.password != register_user_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Confirm password not like password')
    
    user = authenticate_user(register_user_request.username, register_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Email already exists')
    
    if register_user_request.username == Account.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User already exists')
        
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_code = create_access_code(
        data={"email": register_user_request.email, "username": register_user_request.username, "password": bcrypt_context.hash(register_user_request.password)}, 
        expires_delta=token_expires
    )
    
    message = MessageSchema(
        subject="Email Confirmation",
        recipients=[register_user_request.email],
        body=f"Your confirmation code is: {access_code}",
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
    
    return {"message": "Please check your email for the confirmation code"}




@public_router.post("/confirm_code", status_code=status.HTTP_201_CREATED)
async def confirm_email(code: int, email: str, db: Session = Depends(get_db)):
    user_data = pending_users.get(email)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    
    if user_data["access_code"] != code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    
    if datetime.utcnow() > user_data["expires_at"]:
        pending_users.pop(email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired code")
    
    new_user = Account(email=email, username=user_data["username"], password=user_data["password"])
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    pending_users.pop(email)
    
    return {"message": "Email confirmed and user registered successfully"}
