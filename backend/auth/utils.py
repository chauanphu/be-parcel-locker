from datetime import timedelta, datetime
from fastapi import Depends, HTTPException
from starlette import status
from sqlalchemy.orm import Session
from models.account import Account
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from database.session import get_db
from auth import SECRET_KEY, ALGORITHM
from passlib.context import CryptContext

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='api/v1/auth/token')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> bytes:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Account).filter(Account.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(username: str, expires_delta: timedelta):
    payload = {'sub': username}
    expires = datetime.utcnow() + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user')
        
        # Query the database for the latest user with the same username
        user = db.query(Account).filter(Account.username == username).order_by(Account.user_id.desc()).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='User not found')
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user')

def check_admin(payload: str = Depends(get_current_user)):
    print('payload: ', payload)
    role = payload.role
    if role != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Only admin can use this endpoint')
    else:
        return payload