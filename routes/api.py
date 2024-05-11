import uuid

from fastapi import APIRouter, Depends, Header
from starlette.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from common.service import create_access_token, handle_username
from models.db import Users, Accounts, Paid
from models.model import LoginData, DeleteAccountData, AddAccountData, ModifyAccountData, PaidData, MonitorData, \
    JsonResponseModel, StopAccountData
from tasks.morning import monitor
from celery.app.control import Control
from app_celery import celery

router = APIRouter()
auth = HTTPBearer()


async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(auth)):
    print("进行tokken验证")
    return credentials


@router.post("/login")
async def login(form: LoginData):
    user = await Users.filter(username=form.username, password=form.password).first()
    if user:
        access_token = create_access_token()
        user.access_token = access_token
        await user.save()
        return JsonResponseModel(success=True, message="", data={"token": access_token, "user_id": user.id})
    return JsonResponseModel(success=True, message="用户名密码错误", data={"token": "", "user_id": ""})


@router.post("/account/delete", dependencies=[Depends(authenticate)])
async def del_account(data: DeleteAccountData):
    if data.uuid:
        await Accounts.filter(uuid=data.uuid, user_id=data.user_id).delete()
    elif data.status:
        await Accounts.filter(status__in=[x.strip() for x in data.status.split(",")], user_id=data.user_id).delete()

    return JSONResponse(content={"message": "删除成功", "success": True}, status_code=200)


@router.post("/account", dependencies=[Depends(authenticate)])
async def add_account(data: AddAccountData):
    user_id = data.user_id
    account_name = handle_username(data.username)
    account_pass = data.password
    for name in account_name:
        account = await Accounts.get_or_none(username=name, user_id=user_id)
        if account:
            account.password = account_pass
        else:
            account = Accounts(user_id=user_id, username=name, password=account_pass, uuid=str(uuid.uuid4()))
        await account.save()
    return JsonResponseModel(success=True, message=f"{data.username} 添加成功", data={})


@router.post("/account/status", dependencies=[Depends(authenticate)])
async def mod_account(data: ModifyAccountData):
    await Accounts.filter(uuid=data.uuid, user_id=data.user_id).update(status=data.status)
    return JSONResponse(content={"message": "更改成功", "success": True}, status_code=200)


@router.post("/account/pay")
async def pay_account(data: PaidData):
    account = await Accounts.get(uuid=uuid, user_id=data.user_id)
    if account:
        account.status = "paid"
        await account.save()
        await Paid(username=account.username, order_str=account.order, user_id=data.user_id).save()
    return JSONResponse(content={"message": "删除成功", "success": True}, status_code=200)


@router.post("/account/start", dependencies=[Depends(authenticate)])
async def start_account(data: MonitorData):
    account = await Accounts.filter(user_id=data.user_id, uuid=data.uuid).first()
    if account:
        user = await account.user.first()
        print(user.__dict__)
        task = monitor.delay({**account.__dict__, "access_token": user.__dict__['access_token'], "email": data.email})
        account.status = "waiting"
        account.task_id = task.id
        await account.save()
        return JsonResponseModel(success=True, message="加入抢票队列", data={})

    return JsonResponseModel(success=False, message="加入抢票队列失败", data={})


@router.get("/accounts", dependencies=[Depends(authenticate)])
async def get_accounts(x_user_id: str = Header(None)):
    accounts = await Accounts.all()
    accounts = [{
        "uuid": account.uuid,
        "username": account.username,
        "password": account.password,
        "details": account.details,
        "status": account.status,
        "order": account.order,
        "user_id": x_user_id,
        "order_time": account.order_time.strftime('%Y年%m月%d日 %H时%M分%S秒') if account.order_time else "",
    } for account in accounts]
    result = process_data(accounts)
    return JsonResponseModel(data=result, success=True, message="")


@router.post("/account/stop", dependencies=[Depends(authenticate)])
async def stop_account(data: StopAccountData):
    celery_control = Control(app=celery)
    await Accounts.filter(uuid=data.uuid, user_id=data.user_id).update(status="free")
    success = celery_control.revoke(data.task_id, terminate=True)
    if success:
        return JsonResponseModel(success=True, message="任务终止", data={})
    return JsonResponseModel(success=False, message="任务终止失败", data={})


def process_data(data):
    free = []
    waiting = []
    pending = []
    for item in data:
        if item['status'] == "free":
            free.append(item)
        elif item['status'] == "waiting":
            waiting.append(item)
        elif item['status'] == "pending":
            pending.append(item)
    return {"free": free, "waiting": waiting, "pending": pending}
