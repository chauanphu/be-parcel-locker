from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from starlette import status
from auth.utils import authenticate_user, create_access_token, get_current_user
from database.session import get_db
from pydantic import BaseModel

from models.account import Account
from models.role import Role

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


class Token(BaseModel):
    access_token: str
    token_type: str

class UserInfo(BaseModel):
    username: str
    role: str

@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user',
                            )
    token = create_access_token(user.username, timedelta(minutes=120))

    return {
        "access_token": token, 
        "token_type": 'bearer'
    }

@router.get("/me", response_model=UserInfo)
async def read_users_me(
        current_user: Account = Depends(get_current_user),
        db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.role_id == current_user.role).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user',
                            )
    return UserInfo(username=current_user.username, role=role.name)

