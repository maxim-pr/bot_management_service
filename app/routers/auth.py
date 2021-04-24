from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.db import db
from app.schemas import User, UserDB, Token, SignUpForm


auth_router = APIRouter()

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(password: str, hashed_password: str) -> bool:
    return crypt_context.verify(password, hashed_password)


def get_password_hash(password: str) -> str:
    return crypt_context.hash(password)


async def get_user(username: str) -> UserDB:
    if username in db:
        user = db.get(username)
        return UserDB(**user)


async def authenticate_user(username: str, password: str) -> Union[UserDB, bool]:
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {"sub": username, "exp": expires}
    jw_token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    return jw_token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDB:
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    except ExpiredSignatureError:
        raise token_expired_exception
    except JWTError:
        raise invalid_token_exception

    username = payload.get("sub")
    if username is None:
        raise invalid_token_exception

    user = await get_user(username)
    if user is None:
        raise invalid_token_exception

    return user


@auth_router.post("/log-in", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/sign-up", response_model=User)
async def sign_up(form_data: SignUpForm = Depends()):
    if form_data.username in db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Such username already exists")
    if form_data.password1 != form_data.password2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords are not the same")
    db[form_data.username] = {
        "username": form_data.username,
        "first_name": form_data.first_name,
        "last_name": form_data.last_name,
        "hashed_password": crypt_context.hash(form_data.password1),
        "bots": []
    }

    return User(**db[form_data.username])


@auth_router.get("/users/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
