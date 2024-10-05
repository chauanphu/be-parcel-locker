from enum import Enum
from typing import Any, Dict

from auth.utils import check_admin, get_current_user
from database.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from models.recipient import Recipient
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

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
    
# # Create new recipient
# @router.post("/", response_model=RecipientRequest)
# def create_recipient(recipient: RecipientRequest, db: Session = Depends(get_db)):
#     new_recipient = Recipient(**recipient.model_dump())
#     db.add(new_recipient)
#     db.commit()
#     db.refresh(new_recipient)
#     return new_recipient

# Get paginated recipients
@router.get("/", response_model=Dict[str, Any], dependencies=[Depends(check_admin)])
def get_paging_recipients(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1)
):
    # Total number of recipients
    total_recipients = db.query(Recipient).count()

    # Fetch paginated list of recipients
    recipients = (
        db.query(Recipient)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    
    # Format the response
    recipient_responses = [
        {
            "recipient_id": recipient.recipient_id,
            "profile_id": recipient.profile_id,
            "name": recipient.name,
            "phone": recipient.phone,
            "email": recipient.email,
            "address": recipient.address,
            "gender": recipient.gender,
        }
        for recipient in recipients
    ]

    # Calculate total pages
    total_pages = (total_recipients + per_page - 1) // per_page

    # Return the paginated response
    return {
        "total": total_recipients,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": recipient_responses
    }

# Get recipient by recipient_id
@router.get("/{recipient_id}", response_model=RecipientResponse)
def get_recipient(recipient_id: int, db: Session = Depends(get_db), ):
    recipient = db.query(Recipient).filter(Recipient.recipient_id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    return recipient

# # A put request to update recipient
# @router.put("/{recipient_id}", response_model=RecipientResponse)
# def update_recipient(recipient_id: int, _recipient: RecipientRequest, db: Session = Depends(get_db)):
#     # Allow for partial updates
#     recipient_data = _recipient.model_dump(exclude_unset=True, exclude_none=True)
#     recipient_data = _recipient.dict()
    
#     address = _recipient.address
#     address_string = f" {address.address_number}, {address.street} Street, {address.ward} Ward, District/City {address.district}"
#     recipient_data['address'] = address_string
    
#     recipient = db.query(Recipient).filter(Recipient.recipient_id == recipient_id).update(recipient_data)
#     # Check if recipient exists
#     # If not, raise an error
#     if not recipient:
#         raise HTTPException(status_code=404, detail="Recipient not found")
    
#     db.commit()
#     return recipient
