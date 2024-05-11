import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from tortoise import Tortoise
from app_celery import celery
from app_redis import get_redis_
from common.email import EmailSender
from celery.signals import task_success, worker_process_init, worker_process_shutdown
from models.db import Accounts
from settings import TORTOISE_ORM
from celery._state import _task_stack

from tickets.desney import Desney

load_dotenv()


@celery.task
def monitor(account: dict):
    desney = Desney(account['username'], account['password'])
    desney.order = "YXBwX2lkPTIwMTkxMDI5Njg3MzE3NjcmYml6X2NvbnRlbnQ9JTdCJTIyb3V0X3RyYWRlX25vJTIyJTNBJTIyMjAyNDA1MTEwNTAxMDAwNjA2ODYlMjIlMkMlMjJwcm9kdWN0X2NvZGUlMjIlM0ElMjJRVUlDS19NU0VDVVJJVFlfUEFZJTIyJTJDJTIydG90YWxfYW1vdW50JTIyJTNBJTIyMTg5LjAwJTIyJTJDJTIyc3ViamVjdCUyMiUzQSUyMiVFNCVCOCU4QSVFNiVCNSVCNyVFOCVCRiVBQSVFNSVBMyVBQiVFNSVCMCVCQyVFNSVCQSVBNiVFNSU4MSU4NyVFNSU4QyVCQSVFNCVCQSVBNyVFNSU5MyU4MSUyMiUyQyUyMnBhc3NiYWNrX3BhcmFtcyUyMiUzQSUyMjE2MzM2NzkwJTIyJTJDJTIydGltZW91dF9leHByZXNzJTIyJTNBJTIyMjltJTIyJTJDJTIyZXh0ZW5kX3BhcmFtcyUyMiUzQSU3QiUyMnN5c19zZXJ2aWNlX3Byb3ZpZGVyX2lkJTIyJTNBJTIyMjA4ODEyMTg1MDU0OTYzMCUyMiU3RCU3RCZjaGFyc2V0PXV0Zi04Jm1ldGhvZD1hbGlwYXkudHJhZGUuYXBwLnBheSZub3RpZnlfdXJsPWh0dHBzJTNBJTJGJTJGcHJvZC5vcmlnaW4tcG13LnNoYW5naGFpZGlzbmV5cmVzb3J0LmNvbSUyRmdsb2JhbC1wb29sLW92ZXJyaWRlLUElMkZwYXltZW50LW1pZGRsZXdhcmUtc2VydmljZSUyRnRyYW5zYWN0aW9uJTJGYWxpcGF5JTJGY29uZmlybSUyRjE2MzM2NzkwJnNpZ249UUtvTjVhZlM4Rk9IdGdTeWcwZHozRjlNZCUyRjRnOUVCY01vN2w1QXMlMkZUV240eElqeG5JUk9XM0NnNXJ3Q29hJTJCJTJCSEJYcjMzbUhLRVBjYUVSM0Zxc29iZUZpYVgxWTlaaFFORWFKc2Z3cDF3N0s4JTJCYzNnWWpKd3hrVE1HUjdxdUh3SmRsdlVJdzZCZzAxWVglMkI1dmdCVWdaSkxRU3VNYnAlMkJ2TnNFbHNKWUslMkIyZSUyRnNiSTFGeUIyc2lwY2JTMFBHdEVLdm15NkI5TEpyQ0ZUQVZpdyUyRlZKMUdQRThKTjYyVDBPZSUyQlFvJTJCdjJ3V2dWbU11V3VqbUp1Ulk3a05PWlJwNDg2djdKQ1ZTSEdjQ1dLcG9IWHhWZUZjUWE3cFdDbnVQZEx2eiUyRkZQMEducnJ5JTJGMG1rZWNvQm1NbmZvZTJPMWRQNVhLZEFPbFhZOGduZzdSaDFDakpCRVJHQSUzRCUzRCZzaWduX3R5cGU9UlNBMiZ0aW1lc3RhbXA9MjAyNC0wNS0xMSsxNyUzQTU2JTNBMzMmdmVyc2lvbj0xLjA="
    try:
        # desney.login().syn_token().get_eligible().get_morning_price().pay_morning_order().pay_transactiona()
        account['order'] = desney.order
    except StopIteration:
        account['details'] = desney.get_message()
    except Exception:
        account['details'] = desney.get_message()
    return account


async def update_account_status(uuid: str, order: str, details: str):
    await Accounts.filter(uuid=uuid.strip()).update(status="pending",
                                                    details=details,
                                                    order=order,
                                                    order_time=datetime.now())


@task_success.connect(sender=monitor)
def handle_success(**kwargs):
    result = kwargs.get('result')
    asyncio.get_event_loop().run_until_complete(
        update_account_status(result['uuid'], result['order'], result['details']))
    notify.delay(result['access_token'], json.dumps({
        "code": 0,
        "message": f"抢票成功，请及时付款, 账号名: {result['username']}"
    }))
    send_email.delay(result['email'], result['username'], result['password'])


@celery.task()
def notify(token: str, message: str):
    r = get_redis_()
    r.lpush(token, message)
    r.expire(token, 60 * 30)
    return message


@celery.task()
def send_email(email_address: str, username: str, password: str):
    print(f"send_email: {email_address}, username {username},password {password}")
    email = EmailSender()
    address = os.getenv("RECEIVED").split(",")
    if email:
        address = email_address.split(",")
    email.send_msg('你有新的订单', address,
                   email.get_morning_success_body(username=username, password=password))
    return "success"


@worker_process_init.connect
def on_worker_init(*args, **kwargs):
    if _task_stack.top is not None:
        loop = _task_stack.top.request.loop  # Get the event loop for the current task
    else:
        loop = asyncio.get_event_loop()
    loop.run_until_complete(Tortoise.init(config=TORTOISE_ORM))


@worker_process_shutdown.connect
def on_worker_shutdown(*args, **kwargs):
    if _task_stack.top is not None:
        loop = _task_stack.top.request.loop  # Get the event loop for the current task
    else:
        loop = asyncio.get_event_loop()
    loop.run_until_complete(Tortoise.close_connections())
