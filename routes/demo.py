import datetime
import json
from fastapi import APIRouter
from starlette.responses import JSONResponse

from common.service import create_access_token
from models.db import Users, Accounts
from models.model import SendMessageData, SendEmailData, JsonResponseModel, CreateUserData, CreateAccountData
from tasks.morning import notify, send_email

demo_router = APIRouter()


@demo_router.post("/send_msg")
async def send_message(data: SendMessageData):
    task = notify.delay(data.token, json.dumps(data.message.dict()))
    return JSONResponse(content={"code": 0, "message": f"task id is {task.id}"}, status_code=200)


@demo_router.post("/send_email")
async def send_message(data: SendEmailData):
    task = send_email.delay(data.email.split(","), data.username, data.password)
    return JSONResponse(content={"code": 0, "message": f"task id is {task.id}"}, status_code=200)


@demo_router.post("/user")
async def create_user(data: CreateUserData):
    access_token = create_access_token()
    print(type(access_token))
    user = Users(username=data.username,
                 password=data.password,
                 access_token=str(access_token))

    await user.save()
    return JsonResponseModel(success=True, message="创建成功")


@demo_router.post("/account")
async def create_account(data: CreateAccountData):
    user = await Users.filter(access_token=data.token).first()
    if user:
        account = Accounts(username=data.username,
                           password=data.password,
                           status=data.status,
                           uuid=str(datetime.datetime.now().timestamp()),
                           user=user)
        await account.save()
        return JsonResponseModel(success=True, message="创建成功")
    return JsonResponseModel(success=False, message="用户不存在")


@demo_router.get("/")
async def send_message():
    return JsonResponseModel(success=True, message="Hello World")
