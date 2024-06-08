import asyncio
import logging
import os
from datetime import datetime
import pytz
from celery.app.control import Control
from dotenv import load_dotenv
from tortoise import Tortoise
from app_celery import celery
from app_redis import get_redis_
from common.email import EmailSender
from celery.signals import task_success, worker_process_init, worker_process_shutdown
from models.db import Accounts, Task, History
from settings import TORTOISE_ORM
from celery._state import _task_stack
from tickets.desney import Desney
import requests

load_dotenv()
file_handler = logging.FileHandler(filename="/app/logs/task.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger("tasks")
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


async def get_pending_tasks():
    tasks = await Task.filter(status="started").all()
    for task in tasks:
        logger.info(
            f"得到新的任务: username {task.username}, category {task.category}, targetDay {task.targetDay}, count {task.count}")
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
    return tasks


async def get_stopped_tasks():
    celery_control = Control(app=celery)
    tasks = await Task.filter(status="stopped").all()
    for task in tasks:
        task.status = ""
        await task.save()
        task_id = task.task_id
        celery_control.revoke(task_id, terminate=True)


@celery.task
def run_task():
    asyncio.get_event_loop().run_until_complete(get_pending_tasks())


@celery.task
def stop_task():
    asyncio.get_event_loop().run_until_complete(get_pending_tasks())


@celery.task
def one(account: dict, day, count):
    logger.info("开始一日票抢票")
    desney = Desney(account['username'], account['password'], day, count)
    try:
        desney = desney.check_one_day().login().syn_token().get_one_day_mock().get_token().get_one_day_order().pay_transactiona()
        # desney = desney.check_one_day().login().syn_token().get_one_day_mock().get_token().get_one_day_order()
        if desney.order:
            account['order'] = desney.order
            account['success'] = True
        else:
            account['success'] = False
    except StopIteration:
        account['success'] = False
        account['details'] = ", ".join(desney.get_message())
    except Exception:
        account['success'] = False
        account['details'] = ", ".join(desney.get_message())
    return account


@celery.task
def monitor(account: dict):
    logger.info("开始早享卡抢票")
    desney = Desney(account['username'], account['password'])
    try:
        desney = desney.login().syn_token().get_eligible().get_morning_price().pay_morning_order().pay_transactiona()
        # desney = desney.login().syn_token().get_eligible().get_morning_price()
        if desney.order:
            account['order'] = desney.order
            account['success'] = True
        else:
            account['success'] = False
    except StopIteration:
        account['success'] = False
        account['details'] = ", ".join(desney.get_message())
    except Exception:
        account['success'] = False
        account['details'] = ", ".join(desney.get_message())
    return account


async def update_account_status(uuid: str, order: str, details: str, status: str):
    await Accounts.filter(uuid=uuid.strip()).update(status=status,
                                                    details=details,
                                                    order=order,
                                                    order_time=datetime.now())


async def update_task_status(id: int, details: str, order: str, status: str):
    logger.info(f"update_task_status: {id}, {details}, {order}, {status}")
    order_time = None
    if status == "success":
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        shanghai_now = datetime.now(shanghai_tz)
        order_time = shanghai_now.strftime("%Y-%m-%d %H:%M:%S")

    await Task.filter(id=id).update(status=status, details=details, orderTime=order_time, order=order)


async def create_history(account: dict):
    history = History(username=account['username'],
                      targetDay=account['targetDay'],
                      order=account['order'],
                      orderTime=account['orderTime'])
    await history.save()


@task_success.connect(sender=one)
@task_success.connect(sender=monitor)
def handle_success(**kwargs):
    result = kwargs.get('result')
    if result['success']:
        asyncio.get_event_loop().run_until_complete(
            update_task_status(result['id'], result['details'], result['order'], "success"))
        asyncio.get_event_loop().run_until_complete(create_history(result))
        send_email.delay(result['email'], result['username'], result['password'])
    else:
        asyncio.get_event_loop().run_until_complete(
            update_task_status(result['id'], result['details'], result['order'], "error"))


@celery.task()
def notify(token: str, message: str):
    r = get_redis_()
    r.lpush(token, message)
    r.expire(token, 60 * 30)
    return message


@celery.task()
def send_email(email_address: str, username: str, password: str):
    logger.info(f"send_email: {email_address}, username {username},password {password}")
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


token = "YXBwX2lkPTIwMTkxMDI5Njg3MzE3NjcmYml6X2NvbnRlbnQ9JTdCJTIyb3V0X3RyYWRlX25vJTIyJTNBJTIyMjAyNDA1MjkwNTAxMDAwNjQ1ODUlMjIlMkMlMjJwcm9kdWN0X2NvZGUlMjIlM0ElMjJRVUlDS19NU0VDVVJJVFlfUEFZJTIyJTJDJTIydG90YWxfYW1vdW50JTIyJTNBJTIyNTk5LjAwJTIyJTJDJTIyc3ViamVjdCUyMiUzQSUyMiVFNCVCOCU4QSVFNiVCNSVCNyVFOCVCRiVBQSVFNSVBMyVBQiVFNSVCMCVCQyVFNSVCQSVBNiVFNSU4MSU4NyVFNSU4QyVCQSVFNCVCQSVBNyVFNSU5MyU4MSUyMiUyQyUyMnBhc3NiYWNrX3BhcmFtcyUyMiUzQSUyMjE2NzcyNjYxJTIyJTJDJTIydGltZW91dF9leHByZXNzJTIyJTNBJTIyMjltJTIyJTJDJTIyZXh0ZW5kX3BhcmFtcyUyMiUzQSU3QiUyMnN5c19zZXJ2aWNlX3Byb3ZpZGVyX2lkJTIyJTNBJTIyMjA4ODEyMTg1MDU0OTYzMCUyMiU3RCU3RCZjaGFyc2V0PXV0Zi04Jm1ldGhvZD1hbGlwYXkudHJhZGUuYXBwLnBheSZub3RpZnlfdXJsPWh0dHBzJTNBJTJGJTJGcHJvZC5vcmlnaW4tcG13LnNoYW5naGFpZGlzbmV5cmVzb3J0LmNvbSUyRmdsb2JhbC1wb29sLW92ZXJyaWRlLUIlMkZwYXltZW50LW1pZGRsZXdhcmUtc2VydmljZSUyRnRyYW5zYWN0aW9uJTJGYWxpcGF5JTJGY29uZmlybSUyRjE2NzcyNjYxJnNpZ249SDNSbE1ZeThTME5memYxUnBTJTJGVWJxa1dGN2RseThTTEFzd1E5VjZFeUZGZk9HeUVFNUxvM254cHoydHclMkZHNFNjVm1JZUVyRnRWMk5YeXhVeVY1M2hhRGVnTU5RbDNJYXZ4R3U4ZXdtcGo2ZnhuM1hDQlR6aGc4WlJTVGRHZDc1ckxwQVd0TDljMUQzWVN1WlFRM29IYm90S1RtMFkxR2pVaFp5WDhnVVpBSHdrRzBueSUyRkdyTkFLSDR3SlNCeTQlMkJKeEtmbjlVbHRncHRYenJjNUlYT0FORlV4cTd1bWJXNkZNNjkzSnBNZEhaMmF3eGdUckFra1Y5QWhKbWtwMjJSWnVSZmpOYUpTJTJCY1dIYVlOY1pTZnNLeTd2UDhsVFRwR0NNVTJXeEFCU3ZnOWNHdUhzS0RabDhSbjFndGZIUVQlMkZzcEZZNUtNRjBIbVBvWkhHZGtWdjRRJTNEJTNEJnNpZ25fdHlwZT1SU0EyJnRpbWVzdGFtcD0yMDI0LTA1LTI5KzIwJTNBNDklM0E0MSZ2ZXJzaW9uPTEuMA"


def get_link(order: str):
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    }

    response = requests.post(
        f'http://localhost:8090/api/getPaymentLink?order={order}&base64=true',
        headers=headers,
    )
    return response.json().get('data', "")


if __name__ == '__main__':
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # print(get_link(token))
