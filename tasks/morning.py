from app_celery import celery
from app_redis import get_redis_
from common.email import EmailSender
from models.db import Users, Accounts


@celery.task
async def monitor(username: str, password: str, token: str):
    pass
    await Accounts.filter(username=username, password=password).update(order="")
    return "success"


@celery.task()
async def notify(token: str, message: str):
    r = get_redis_()
    r.lpush(token, message)
    return "success"


@celery.task()
def send_email(address: str, username: str, password: str):
    email = EmailSender()
    email.send_msg('你有新的订单', address,
                   email.get_morning_success_body(username=username, password=password))
    return "success"
