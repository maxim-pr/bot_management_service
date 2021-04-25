from fastapi import Form
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                                ".eyJzdWIiOiI2MDg1ZGVlNmUyOGVjOTgzZTE4YWNiYWEiLCJleHAiOjE2MTkzOTA3MzR9"
                                ".Wjb9FhZqjrGXH9YpJjU3hcmaA7FfmHDXvxCuWORizsM",
                "token_type": "bearer"
            }
        }


class Bot(BaseModel):
    bot_token: str

    class Config:
        schema_extra = {
            "example": {
                "bot_token": "4050878952:aJCcyEMTdkch2mQjgxxLzOvn5MKmWZWpQyt"
            }
        }


class Bots(BaseModel):
    bots: list[Bot]

    class Config:
        schema_extra = {
            "example": {
                "bots": [
                    {
                        "bot_token": "4050878952:aJCcyEMTdkch2mQjgxxLzOvn5MKmWZWpQyt"
                    },
                    {
                        "bot_token": "4659848255:tJgcwEgTdkah2gQjexxjxOen5tKmvZWxQwt"
                    }
                ]

            }
        }


# model for endpoints' result
class UserBase(BaseModel):
    username: str
    first_name: str = None
    last_name: str = None
    bots: list[Bot]

    class Config:
        schema_extra = {
            "example": {
                "username": "ivan4",
                "first_name": "Ivan",
                "last_name": "Ivanov",
                "bots": [
                    {
                        "bot_token": "4050878952:aJCcyEMTdkch2mQjgxxLzOvn5MKmWZWpQyt"
                    }
                ]
            }
        }


# database model
class User(UserBase):
    user_id: str
    hashed_password: str


class UserWithoutId(UserBase):
    hashed_password: str


class SignUpForm:
    def __init__(self,
                 username: str = Form(...),
                 first_name: str = Form(None),
                 last_name: str = Form(None),
                 password1: str = Form(...),
                 password2: str = Form(...)
                 ):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.password1 = password1
        self.password2 = password2





