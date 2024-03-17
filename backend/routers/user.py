import uuid
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

class Role(BaseModel):
    role_id: uuid.uuid4
    name_role: str

class UserRequest(BaseModel):
    user_id: uuid.uuid4
    username: str
    password: str
    email: str
    role: Role

#cho phép tạo mà k cần nhập profile
    
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

# A POST REQUEST TO CREATE USER
    #tạo cần profile
@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user_with_profile(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
    # user_id = str(uuid.uuid1())
    # create_user_request.user_id = user_id
    user = authenticate_user(create_user_request.username, create_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User already exists')
    create_user_request.password = bcrypt_context.hash(create_user_request.password)
    db_user = User(**create_user_request.model_dump())
    print(db_user)
    db.add(db_user)
    db.commit()
    return {"messsage": "User created successfully"}


#tạo k cần profile
@router.post('/noneed', status_code=status.HTTP_201_CREATED)
async def create_user_without_profile(create_free_user:UserRequest, db:Session = Depends(get_db)):
    # user_id = str(uuid.uuid1())
    # create_free_user.user_id = user_id
    user = authenticate_user(create_free_user.username, create_free_user.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='User already exists')
    create_free_user.password = bcrypt_context.hash(create_free_user.password)
    db_user = User(**create_free_user.model_dump())
    print(db_user)
    db.add(db_user)
    db.commit()
    return {"messsage": "User created successfully"}
    
    #TODO: login cho k cần profile


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# A PUT REQUEST TO UPDATE USER
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, _user: UserRequest, db: Session = Depends(get_db)):
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

