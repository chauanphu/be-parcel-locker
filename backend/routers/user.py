from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database.session import get_db
from database import session
from models.user import User
from sqlalchemy.orm import Session
router = APIRouter(
    prefix="/user",
    tags=["user"],
)

class UserRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str

@router.get("/{user_id}", response_model=UserRequest)
def get_user(user_id: int, db: Session = Depends(get_db), ):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# A PUT REQUEST TO UPDATE USER
@router.put("/{user_id}", response_model=UserRequest)
def update_user(user_id: int, user: UserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = user.name
    user.email = user.email
    user.phone = user.phone
    user.address = user.address
    db.commit()
    return user

# TODO: Implement PUT CHANGE PASSWORD
