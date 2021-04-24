from fastapi import Form
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    first_name: str = None
    last_name: str = None


class UserDB(User):
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


class Bot(BaseModel):
    bot_token: str


class Bots(BaseModel):
    bots: list[Bot]
