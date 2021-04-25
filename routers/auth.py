from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from loader import auth_router, db
from schemas import UserBase, UserWithoutId, User, Token, SignUpForm

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(password: str, hashed_password: str) -> bool:
    return crypt_context.verify(password, hashed_password)


def get_password_hash(password: str) -> str:
    return crypt_context.hash(password)


async def authenticate_user(username: str, password: str) -> Union[User, bool]:
    try:
        user = await db.get_user_by_username(username)
    except KeyError:
        return False

    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {"sub": user_id, "exp": expires}
    jw_token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    return jw_token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid access token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token has expired",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    except ExpiredSignatureError:
        raise token_expired_exception
    except JWTError:
        raise invalid_token_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise invalid_token_exception

    try:
        user = await db.get_user_by_id(user_id)
    except KeyError:
        raise invalid_token_exception

    return user


@auth_router.post("/log-in",
                  response_model=Token,
                  description="Log in with username and password",
                  response_description="Returns access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.user_id)
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/sign-up",
                  response_model=UserBase,
                  description="Sign up",
                  response_description="Returns current user's data")
async def sign_up(form_data: SignUpForm = Depends()):
    if await db.exists(form_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    if form_data.password1 != form_data.password2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords are not the same")

    # add user to the database
    user_id = await db.add_user(UserWithoutId(username=form_data.username,
                                              first_name=form_data.first_name,
                                              last_name=form_data.last_name,
                                              hashed_password=crypt_context.hash(form_data.password1)))
    user = await db.get_user_by_id(user_id)
    return UserBase(**user.dict())


@auth_router.get("/me", response_model=UserBase, description="Get information about user")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserBase(**current_user.dict())
