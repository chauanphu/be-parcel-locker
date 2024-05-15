from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.session import get_db
from models.user import User
from sqlalchemy.orm import Session
from typing import Optional
from auth.utils import get_current_user, authenticate_user, bcrypt_context
from starlette import status

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(get_current_user)]
)
router2 = APIRouter(
    prefix="/user2",
    tags=["user2"]
)

class UserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CreateUserRequest(BaseModel):
    email: str
    username: str
    name: str
    address: str
    phone: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    phone: str
    address: str

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), ):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# A PUT REQUEST TO UPDATE USER
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, _user: UserRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    user = db.query(User).filter(User.user_id == user_id).update(
        _user.model_dump(
            exclude_unset=True, 
            exclude_none=True
        ))
    # Check if user exists
    # If not, raise an error
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.commit()
    return user

# A POST REQUEST TO CREATE USER
@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
    user = authenticate_user(create_user_request.email, create_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Email already exists')
    create_user_request.password = bcrypt_context.hash(create_user_request.password)
    db_user = User(**create_user_request.model_dump())
    print(db_user)
    db.add(db_user)
    db.commit()
    return {"messsage": "User created successfully"}

@router2.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
    user = authenticate_user(create_user_request.email, create_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Email already exists')
    create_user_request.password = bcrypt_context.hash(create_user_request.password)
    db_user = User(**create_user_request.model_dump())
    print(db_user)
    db.add(db_user)
    db.commit()
    return {"messsage": "User created successfully"}
