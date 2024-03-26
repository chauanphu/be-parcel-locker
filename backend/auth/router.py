from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from starlette import status
from auth.utils import authenticate_user, create_access_token, bcrypt_context
from database.session import get_db
from models.user import Account
from pydantic import BaseModel
import uuid

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user',
                            )
    token = create_access_token(user.username, timedelta(minutes=20))

    return {
        "access_token": token, 
        "token_type": 'bearer'
    }

class CreateAccountRequest(BaseModel):
    username: str
    password: str
    role_id: int


class AccountResponse(BaseModel):
    user_id: str
    username: str

@router.post("/account")
def create_account(account: CreateAccountRequest, db: Session = Depends(get_db)):
    account_exists = db.query(Account).filter(Account.username == account.username).first()
    if account_exists:
        raise HTTPException(status_code=status.HTTP_400, detail="Account already exists")
    new_account = Account(
        user_id=uuid.uuid4(),
        username=account.username,
        password=bcrypt_context.hash(account.password),
        role_id=account.role_id
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

# @router.get("/login", status_code=status.HTTP_200_OK)
# async def user(current_user: User = Depends(get_current_user)):
#     if current_user is None:
#         raise HTTPException(status_code=401, detail='Authentication Failed')
#     return {"User": user}

# @router.post("/login")
# def login(email:str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"Invalid Credentials")
#     return user