from fastapi import APIRouter
from starlette.responses import JSONResponse

from common.service import create_access_token
from models.db import Users
from models.model import LoginData

router = APIRouter()


@router.post("/login")
async def login(form: LoginData):
    user = await Users.filter(username=form.username, password=form.password).first()
    if user:
        access_token = create_access_token()
        user.access_token = access_token
        await user.save()
        return JSONResponse(content={"token": access_token, "success": True, "message": ""}, status_code=200)
    return JSONResponse(content={"token": "", "success": False, "message": "用户名密码错误"}, status_code=200)
