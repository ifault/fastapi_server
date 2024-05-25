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
def one(account: dict, day, count):
    desney = Desney(account['username'], account['password'], day, count)
    try:
        desney = desney.check_one_day().login().syn_token().get_one_day_mock().get_token().get_one_day_order().pay_transactiona()
        if desney.order:
            account['order'] = desney.order
            account['success'] = True
        else:
            account['success'] = False
    except StopIteration:
        account['success'] = False
        account['details'] = desney.get_message()
    except Exception:
        account['success'] = False
        account['details'] = desney.get_message()
    return account


@celery.task
def monitor(account: dict):
    desney = Desney(account['username'], account['password'])
    try:
        desney = desney.login().syn_token().get_eligible().get_morning_price().pay_morning_order().pay_transactiona()
        account['order'] = desney.order
        account['success'] = True
    except StopIteration:
        account['success'] = False
        account['details'] = desney.get_message()
    except Exception:
        account['success'] = False
        account['details'] = desney.get_message()
    return account


async def update_account_status(uuid: str, order: str, details: str, status: str):
    await Accounts.filter(uuid=uuid.strip()).update(status=status,
                                                    details=details,
                                                    order=order,
                                                    order_time=datetime.now())


@task_success.connect(sender=one)
@task_success.connect(sender=monitor)
def handle_success(**kwargs):
    result = kwargs.get('result')
    print(result['success'])
    if result['success']:
        asyncio.get_event_loop().run_until_complete(
            update_account_status(result['uuid'], result['order'], result['details'], 'pending'))
        notify.delay(result['access_token'], json.dumps({
            "code": 0,
            "message": f"抢票成功，请及时付款, 账号名: {result['username']}"
        }))
        send_email.delay(result['email'], result['username'], result['password'])
    else:
        asyncio.get_event_loop().run_until_complete(
            update_account_status(result['uuid'], "", result['details'], 'free'))


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
