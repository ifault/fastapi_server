from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from common.service import create_access_token
from models.db import User, Task
from models.model import LoginData, JsonResponseModel, StartTaskData
from tasks.morning import one, monitor, send_email as se
from app_celery import celery
from tickets.desney import Desney

router = APIRouter()
auth = HTTPBearer()


def convertDate(date):
    return datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d") if date else None


def convertDateToCn(date):
    return datetime.strptime(date, "%Y%m%d").strftime("%Y年%m月%d日") if date else None


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


@router.post("/start")
async def start(data: StartTaskData):
    task = await Task.get(id=data.id)
    task.status = "running"
    task.details = ""
    await task.save()
    date = task.targetDay
    date = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d") if date else None
    targetDay = convertDateToCn(task.targetDay)
    if task.category == "oneday":
        tt = one.delay(task.to_dict(), date, task.count, task.id)
        task.taskId = tt.id
        await task.save()
    elif task.category == "morning":
        tt = monitor.delay(task.to_dict(), task.id, targetDay=targetDay)
        task.taskId = tt.id
        await task.save()
    return JsonResponseModel(success=True, message="创建成功", data={})





@router.post("/check")
async def check(data: StartTaskData):
    task = await Task.get(id=data.id)
    day = convertDate(task.targetDay)
    morning_target_day = convertDateToCn(task.targetDay)
    desney = Desney(task.username,
                    task.password,
                    day,
                    task.count,
                    targetDay=morning_target_day
                    )
    try:
        if task.category == "oneday":
            desney = desney.login()
        elif task.category == "morning":
            desney = desney.login().syn_token().get_eligible()
        task.status = "ready"
        await task.save()
    except Exception:
        pass
    task.cardCount = desney.quantity
    task.details = desney.messages[-1] if len(desney.messages) > 0 else ""
    await task.save()
    return JsonResponseModel(success=True, message="查询成功", data=task.to_dict())


@router.post("/stop/{task_id}")
async def stop(task_id: str):
    res = celery.control.revoke(task_id, terminate=True)
    task = await Task.get(taskId=task_id)
    task.status = "ready"
    await task.save()
    return JsonResponseModel(success=True, message="停止成功", data={})


@router.post("/send_email")
async def send_email():
    se.delay()
    return JsonResponseModel(success=True, message="发送成功", data={})
