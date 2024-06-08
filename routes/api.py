import base64
import json
import uuid
from pprint import pprint
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Header
from starlette.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from common.service import create_access_token, handle_username, is_valid_id, is_valid_date
from models.db import Users, Accounts, Paid, Task
from models.model import LoginData, DeleteAccountData, AddAccountData, ModifyAccountData, PaidData, MonitorData, \
    JsonResponseModel, StopAccountData, OneDayAccountData
from tasks.morning import monitor, one
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
    account = await Accounts.filter(uuid=data.uuid, user_id=data.user_id).first()
    # dd = "YXBwX2lkPTIwMTkxMDI5Njg3MzE3NjcmYml6X2NvbnRlbnQ9JTdCJTIyb3V0X3RyYWRlX25vJTIyJTNBJTIyMjAyNDA1MTEwNTAxMDAwNjA2ODYlMjIlMkMlMjJwcm9kdWN0X2NvZGUlMjIlM0ElMjJRVUlDS19NU0VDVVJJVFlfUEFZJTIyJTJDJTIydG90YWxfYW1vdW50JTIyJTNBJTIyMTg5LjAwJTIyJTJDJTIyc3ViamVjdCUyMiUzQSUyMiVFNCVCOCU4QSVFNiVCNSVCNyVFOCVCRiVBQSVFNSVBMyVBQiVFNSVCMCVCQyVFNSVCQSVBNiVFNSU4MSU4NyVFNSU4QyVCQSVFNCVCQSVBNyVFNSU5MyU4MSUyMiUyQyUyMnBhc3NiYWNrX3BhcmFtcyUyMiUzQSUyMjE2MzM2NzkwJTIyJTJDJTIydGltZW91dF9leHByZXNzJTIyJTNBJTIyMjltJTIyJTJDJTIyZXh0ZW5kX3BhcmFtcyUyMiUzQSU3QiUyMnN5c19zZXJ2aWNlX3Byb3ZpZGVyX2lkJTIyJTNBJTIyMjA4ODEyMTg1MDU0OTYzMCUyMiU3RCU3RCZjaGFyc2V0PXV0Zi04Jm1ldGhvZD1hbGlwYXkudHJhZGUuYXBwLnBheSZub3RpZnlfdXJsPWh0dHBzJTNBJTJGJTJGcHJvZC5vcmlnaW4tcG13LnNoYW5naGFpZGlzbmV5cmVzb3J0LmNvbSUyRmdsb2JhbC1wb29sLW92ZXJyaWRlLUElMkZwYXltZW50LW1pZGRsZXdhcmUtc2VydmljZSUyRnRyYW5zYWN0aW9uJTJGYWxpcGF5JTJGY29uZmlybSUyRjE2MzM2NzkwJnNpZ249UUtvTjVhZlM4Rk9IdGdTeWcwZHozRjlNZCUyRjRnOUVCY01vN2w1QXMlMkZUV240eElqeG5JUk9XM0NnNXJ3Q29hJTJCJTJCSEJYcjMzbUhLRVBjYUVSM0Zxc29iZUZpYVgxWTlaaFFORWFKc2Z3cDF3N0s4JTJCYzNnWWpKd3hrVE1HUjdxdUh3SmRsdlVJdzZCZzAxWVglMkI1dmdCVWdaSkxRU3VNYnAlMkJ2TnNFbHNKWUslMkIyZSUyRnNiSTFGeUIyc2lwY2JTMFBHdEVLdm15NkI5TEpyQ0ZUQVZpdyUyRlZKMUdQRThKTjYyVDBPZSUyQlFvJTJCdjJ3V2dWbU11V3VqbUp1Ulk3a05PWlJwNDg2djdKQ1ZTSEdjQ1dLcG9IWHhWZUZjUWE3cFdDbnVQZEx2eiUyRkZQMEducnJ5JTJGMG1rZWNvQm1NbmZvZTJPMWRQNVhLZEFPbFhZOGduZzdSaDFDakpCRVJHQSUzRCUzRCZzaWduX3R5cGU9UlNBMiZ0aW1lc3RhbXA9MjAyNC0wNS0xMSsxNyUzQTU2JTNBMzMmdmVyc2lvbj0xLjA="
    # # encoded_string = "SGVsbG8gV29ybGQ="
    # decoded_bytes = base64.b64decode(dd)
    # decoded_string = decoded_bytes.decode('utf-8')
    # # params_formated = unquote(decoded_string)
    # params = decoded_string.split('&')
    # biz_content_encoded = next(item for item in params if item.startswith('biz_content='))
    # biz_content_encoded = biz_content_encoded.split('=')[1]  # 获取编码后的biz_content值
    # biz_content_decoded = unquote(biz_content_encoded)
    # biz_content_json = json.loads(biz_content_decoded)
    # pprint(biz_content_json)
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
        account.details = ""
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


@router.post("/account/one_day", dependencies=[Depends(authenticate)])
async def one_day_account(data: OneDayAccountData):
    valid = True
    account = await Accounts.filter(user_id=data.user_id, uuid=data.uuid).first()

    if not is_valid_id(data.card):
        account.details = "身份证号码错误"
        valid = False
    date = is_valid_date(data.target_day)
    if not date:
        account.details = "日期格式输入错误"
        valid = False
    if data.count <= 0:
        account.details = "数量输入错误"
        valid = False

    if not valid:
        await account.save()
        return JsonResponseModel(success=False, message="输入错误", data={})

    user = await account.user.first()
    task = one.delay({**account.__dict__, "access_token": user.__dict__['access_token'], "email": data.email}, date, data.count)
    account.details = ""
    account.status = "waiting"
    account.task_id = task.id
    await account.save()

    return JsonResponseModel(success=True, message="任务开始", data={})

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


@router.get("/tasks/{status}")
async def get_tasks(status: str):
    print(status)
    if status == "all":
        return await Task.all()
    return await Task.filter(status=status).all()


@router.post("/order")
async def get_order_demo():
    return JsonResponseModel(success=True, message="success", data={
        "url": "http://www.baidu.com"
    })