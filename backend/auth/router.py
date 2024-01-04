from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from sqlalchemy.orm import Session
from starlette import status
from models.user import User
from auth import bcrypt_context
from auth.utils import authenticate_user, create_access_token, get_current_user
from auth.models import CreateUserRequest, Token
from database.session import get_db

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: CreateUserRequest, db: Session = Depends(get_db)):
    user = authenticate_user(create_user_request.email, create_user_request.password, db)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Email already exists')
    create_user_model = User(
        username = create_user_request.email,
        password = bcrypt_context.hash(create_user_request.password),
        email = create_user_request.email,
        address = create_user_request.address,
        phone = create_user_request.phone
    )
    db.add(create_user_model)
    db.commit()
    return {"message": "User created successfully"}


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user')
    token = create_access_token(user.email, timedelta(minutes=20))

    return {
        'access_token': token, 
        'token_type': 'bearer'
    }

@router.get("/login", status_code=status.HTTP_200_OK)
async def user(current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    return {"User": user}