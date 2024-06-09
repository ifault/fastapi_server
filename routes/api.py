import uuid
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from common.service import create_access_token
from models.db import User
from models.model import LoginData, JsonResponseModel

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
