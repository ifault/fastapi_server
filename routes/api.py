from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from common.service import create_access_token
from models.db import User, Task
from models.model import LoginData, JsonResponseModel
from tasks.morning import one, monitor, send_email as se
from app_celery import celery
router = APIRouter()
auth = HTTPBearer()


async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(auth)):
    print("进行tokken验证")
    return credentials


@router.post("/login")
async def login(form: LoginData):
    user = await User.filter(username=form.username, password=form.password).first()
    if user:
        access_token = create_access_token()
        user.access_token = access_token
        await user.save()
        return JsonResponseModel(success=True, message="", data={"token": access_token, "user_id": user.id})
    return JsonResponseModel(success=True, message="用户名密码错误", data={"token": "", "user_id": ""})


@router.post("/start/{task_id}")
async def start(task_id: int):
    task = await Task.get(id=task_id)
    task.status = "running"
    await task.save()
    date = task.targetDay
    date = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d") if date else None
    if task.category == "oneday":
        tt = one.delay(task.to_dict(), date, task.count)
        task.taskId = tt.id
        await task.save()
    elif task.category == "morning":
        tt = monitor.delay(task.to_dict())
        task.taskId = tt.id
        await task.save()
    return JsonResponseModel(success=True, message="创建成功", data={})


@router.post("/stop/{task_id}")
async def stop(task_id: str):
    res = celery.control.revoke(task_id, terminate=True)
    task = await Task.get(taskId=task_id)
    task.status = None
    await task.save()
    return JsonResponseModel(success=True, message="停止成功", data={})


@router.post("/send_email")
async def send_email():
    se.delay()
    return JsonResponseModel(success=True, message="发送成功", data={})
