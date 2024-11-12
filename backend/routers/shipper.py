from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from models.account import Account
from database.session import get_db
from models.shipper import Shipper
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from auth.utils import get_current_user, hash_password
from starlette import status

router = APIRouter(
    prefix="/shipper",
    tags=["shipper"],
    dependencies=[Depends(get_current_user)]
)

class OrderInforSchema(BaseModel):
    order_id: int
    sending_locker_address: str
    sending_locker_latitude: int
    sending_locker_longitude: int
    receiving_locker_address: str
    receiving_locker_latitude: int
    receiving_locker_longitude: int
    route: Optional[str] = None
    time: Optional[str] = None

class CreateShipperSchema(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str
    role: int = 3
    
@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_shipper(create_shipper_request: CreateShipperSchema, db: Session = Depends(get_db)):
    # Check if passwords match
    if create_shipper_request.password != create_shipper_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')
    
    # Check if the username or email already exists
    existing_user = db.query(Account).filter(
        (Account.username == create_shipper_request.username) 
        (Account.email == create_shipper_request.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username or email already exists')
    
    # Hash the password
    hashed_password = hash_password(create_shipper_request.password)
    
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

#GET PAGING SHIPPER
@router.get("/", response_model=Dict[str, Any])
def get_paging_shippers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    # Total number of shippers
    total_shippers = db.query(Shipper).count()

    # Fetch paginated list of shippers
    shippers = db.query(Shipper).offset((page - 1) * per_page).limit(per_page).all()

    # Format the response
    shipper_responses = [
        {
            "shipper_id": shipper.shipper_id,
            "order_id": shipper.order_id,
            "name": shipper.name,
            "gender": shipper.gender,
            "age": shipper.age,
            "phone": shipper.phone,
            "address": shipper.address,
        }
        for shipper in shippers
    ]

    total_pages = (total_shippers + per_page - 1) // per_page
    return {
        "total": total_shippers,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": shipper_responses
    }