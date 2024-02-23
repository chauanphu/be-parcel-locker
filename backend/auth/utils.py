from datetime import timedelta, datetime
from fastapi import Depends, HTTPException
from starlette import status
from sqlalchemy.orm import Session
from models.user import User
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from database.session import get_db
from auth import SECRET_KEY, ALGORITHM, bcrypt_context

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(username: str, expires_delta: timedelta):
    payload = {'sub': username}
    expires = datetime.utcnow() + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        # user = db.query(User).filter(User.username == username).first()
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user')
        return {'username': username}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user')

