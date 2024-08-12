from datetime import datetime, timedelta
from sqlalchemy import DateTime
from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
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
    prefix="/recipients",
    tags=["recipients"],
    dependencies=[Depends(get_current_user)]
)



