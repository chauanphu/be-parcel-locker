import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.session import get_db
from models.user import Account, Profile
from sqlalchemy.orm import Session
from typing import Optional
from auth.utils import get_current_user, bcrypt_context
from starlette import status

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(get_current_user)]
)

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

@router.post("/", response_model=UserResponse)
def create_user_with_profile(user: CreateUserRequest, db: Session = Depends(get_db)):
    # check if user already exists
    user_exists = db.query(Account).filter(Account.email == user.email).first()
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    # create user
    new_user = Account(
        user_id=uuid.uuid4(),
        email=user.email,
        username=user.username,
        password=bcrypt_context.hash(user.password),
        role_id=1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # create profile
    new_profile = Profile(
        user_id=new_user.user_id,
        first_name=user.name,
        last_name=user.name,
        phone_number=user.phone
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_user