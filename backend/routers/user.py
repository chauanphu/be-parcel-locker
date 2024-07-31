from datetime import datetime, timedelta
from sqlalchemy import DateTime
from fastapi import APIRouter, HTTPException, Depends,Query
from pydantic import BaseModel, EmailStr, Field
from database.session import get_db
from models.user import User
from models.order import Order
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from auth.utils import get_current_user, authenticate_user, bcrypt_context
from starlette import status
from enum import Enum

class StatusEnum(str, Enum):
    Active = 'Active'
    Inactive = 'Inactive'
    Blocked = 'Blocked'

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(get_current_user)]
)

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

# # Check theo user_id nếu quá 3 tháng không gửi/ nhận order -> inactive
# def check_user_status(user_id: int, db: Session = Depends(get_db)):
#     """
#     Checks all accounts and updates the status to 'Inactive' if they have not created or received any order for 3 months.

#     Parameters:
#     - db (Session): The database session to use for the query.

#     Returns:
#     - inactive_user: All user_id that is inactive
#     """
#     three_months_ago = datetime.utcnow() - timedelta(days=90)
    
#     # Check if the account has created or received any orders in the past 3 months
#     recent_order_exists = db.query(Order).filter(
#         (Order.sender_id == user_id) | (Order.recipient_id == user_id),
#         (Order.ordering_date >= three_months_ago) | (Order.receiving_date >= three_months_ago)
#     ).first()
        
#     # If no recent orders found, update the account status to 'Inactive'
#     if not recent_order_exists:
#         query = db.query(User).filter(User.user_id == user_id).update({"status": "Inactive"})
#         db.commit()
#         # return query



@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), ):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=Dict[str, Any])
def get_paging_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):

        # Total number of users
        total_users = db.query(User).count()

        # Fetch paginated list of users
        users = db.query(User).offset((page - 1) * per_page).limit(per_page).all()

        # Format the response
        user_responses = [
            {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "address": user.address,
                "status": user.status,
                "Date_created": user.Date_created,
                "role": user.role,
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
    
    
    user_data = create_user_request.dict()
    
    
    address = create_user_request.address
    address_string = f" {address.address_number}, {address.street} Street, {address.ward} Ward, District/City {address.district}"
    user_data['address'] = address_string
    db_user = User(**user_data)
    
    print(db_user)
    db.add(db_user)
    db.commit()
    return {"messsage": "User created successfully"}

# @router2.post('/', status_code=status.HTTP_201_CREATED)
# async def create_user(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
#     user = authenticate_user(create_user_request.email, create_user_request.password, db)
#     if user:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
#                             detail='Email already exists')
#     create_user_request.password = bcrypt_context.hash(create_user_request.password)
#     db_user = User(**create_user_request.model_dump())
#     print(db_user)
#     db.add(db_user)
#     db.commit()
#     return {"messsage": "User created successfully"}

# register user
@router.post('/Register', status_code=status.HTTP_201_CREATED)
async def register_user(register_user_request: RegisterUserRequest, db: Session = Depends(get_db)):
    if register_user_request.password != register_user_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Confirm password not like password')
    user = authenticate_user(register_user_request.email, register_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Email already exists')
    hashed_password = bcrypt_context.hash(register_user_request.password)
    user_data = {
        "username": register_user_request.username,
        "email": register_user_request.email,
        "password": hashed_password,
    }
    db_user = User(**user_data)
    
    db.add(db_user)
    db.commit()
    return {"message": "User registered successfully"}
