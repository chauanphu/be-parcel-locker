from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from database.session import get_db
from models.recipient import Recipient
from sqlalchemy.orm import Session
from auth.utils import get_current_user
from enum import Enum

router = APIRouter(
    prefix="/recipient",
    tags=["recipient"],
    dependencies=[Depends(get_current_user)]
)

public_router = APIRouter(
    prefix="/recipient",
    tags=["recipient"]
)


class GenderStatusEnum(str, Enum):
    Male = 'Male'
    Female = 'Female'
    NoResponse = 'Prefer not to respond'

class Address(BaseModel):
    address_number: str
    street: str
    ward: str
    district: str

class RecipientRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    address: Address
    gender: GenderStatusEnum

class RecipientResponse(BaseModel):
    recipient_id: int
    name: str
    phone: str
    email: EmailStr
    address: Address
    gender: GenderStatusEnum
    
# Create new recipient
@router.post("/", response_model=RecipientRequest)
def create_recipient(recipient: RecipientRequest, db: Session = Depends(get_db)):
    new_recipient = Recipient(**recipient.model_dump())
    db.add(new_recipient)
    db.commit()
    db.refresh(new_recipient)
    return new_recipient

# Get recipient by recipient_id
@router.get("/{recipient_id}", response_model=RecipientResponse)
def get_recipient(recipient_id: int, db: Session = Depends(get_db), ):
    recipient = db.query(Recipient).filter(Recipient.recipient_id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    return recipient

# A put request to update recipient
@router.put("/{recipient_id}", response_model=RecipientResponse)
def update_recipient(recipient_id: int, _recipient: RecipientRequest, db: Session = Depends(get_db)):
    # Allow for partial updates
    recipient_data = _recipient.model_dump(exclude_unset=True, exclude_none=True)
    recipient_data = _recipient.dict()
    
    address = _recipient.address
    address_string = f" {address.address_number}, {address.street} Street, {address.ward} Ward, District/City {address.district}"
    recipient_data['address'] = address_string
    
    recipient = db.query(Recipient).filter(Recipient.recipient_id == recipient_id).update(recipient_data)
    # Check if recipient exists
    # If not, raise an error
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    db.commit()
    return recipient
