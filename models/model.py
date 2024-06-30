from typing import Optional

from pydantic import BaseModel
import uuid

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
    user_id: str
    status: Optional[str] = "free"


class JsonResponseModel(BaseModel):
    success: bool
    message: str
    data: dict = {}


class APIModel(BaseModel):
    user_id: str


class DeleteAccountData(APIModel):
    uuid: Optional[str] = None
    status: Optional[str] = None


class ModifyAccountData(APIModel):
    uuid: str
    status: str


class StopAccountData(APIModel):
    uuid: str
    task_id: str


class OneDayAccountData(APIModel):
    uuid: str
    target_day: str
    count: int
    card: str
    email: Optional[str]


class AddAccountData(APIModel):
    username: str
    password: str


class PaidData(APIModel):
    uuid: str


class MonitorData(APIModel):
    uuid: str
    email: Optional[str]


class StartTaskData(BaseModel):
    id: str
    schedule: Optional[bool] = False
