from typing import Optional

from pydantic import BaseModel


class SocketResponseData(BaseModel):
    code: int
    message: str


class SendMessageData(BaseModel):
    message: SocketResponseData
    token: str


class SendEmailData(BaseModel):
    email: str
    username: str
    password: str


class LoginData(BaseModel):
    username: str
    password: str


class CreateUserData(BaseModel):
    username: str
    password: str


class CreateAccountData(BaseModel):
    username: str
    password: str
    token: str
    status: Optional[str] = "free"


class JsonResponseModel(BaseModel):
    success: bool
    message: str
    data: dict = {}