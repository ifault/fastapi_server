import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

import pytz
from celery import chain
from dotenv import load_dotenv
from tortoise import Tortoise
from app_celery import celery
from common.email import EmailSender
from celery.signals import task_success, worker_process_init, worker_process_shutdown
from models.db import Task, History
from redis_client import get_redis_client
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


def get_current_time():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    shanghai_now = datetime.now(shanghai_tz)
    return shanghai_now.strftime("%Y-%m-%d %H:%M:%S")


def get_order_time():
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    shanghai_now = datetime.now(shanghai_tz)
    shanghai_now_plus_30_min = shanghai_now + timedelta(minutes=30)
    return shanghai_now_plus_30_min.strftime("%Y-%m-%d %H:%M:%S")


def trace_progress(task_id, info):
    client = get_redis_client()
    client.rpush(f"progress:{task_id}", info)


@celery.task(limit=60 * 60 * 2)
def one(account: dict, day, count):
    logger.info("开始一日票抢票")
    desney = Desney(account['username'],
                    account['password'],
                    day,
                    count,
                    callback=trace_progress,
                    task_id=account['id']
                    )
    try:
        desney = desney.check_one_day().login().syn_token().get_one_day_mock().get_token().get_one_day_order().pay_transactiona()
        # desney = desney.check_one_day()
        if desney.order:
            account['order'] = desney.order
            account['success'] = True
        else:
            account['success'] = False
            account['details'] = "未获取到订单信息，抢票失败"
            trace_progress(account['id'], account['details'])
    except StopIteration:
        account['success'] = False
        account['details'] = desney.messages[-1] if len(desney.messages) > 0 else ""
        trace_progress(account['id'], account['details'])
    except Exception as e:
        account['success'] = False
        account['details'] = desney.messages[-1] if len(desney.messages) > 0 else ""
        trace_progress(account['id'], account['details'])
    return account


@celery.task(limit=60 * 60 * 2)
def monitor(account: dict, targetDay: str):
    logger.info("开始早享卡抢票")
    desney = Desney(account['username'], account['password'], callback=trace_progress, targetDay=targetDay,
                    task_id=account['id'])
    try:
        desney = desney.login().syn_token().get_eligible().check_morning_date().get_morning_price().pay_morning_order().pay_transactiona()
        # desney = desney.login().syn_token().get_eligible().check_morning_date()
        if desney.order:
            account['order'] = desney.order
            account['success'] = True
        else:
            account['success'] = False
    except StopIteration:
        account['success'] = False
        account['details'] = desney.messages[-1] if len(desney.messages) > 0 else ""
        trace_progress(account["id"], account['details'])
    except Exception:
        account['success'] = False
        account['details'] = desney.messages[-1] if len(desney.messages) > 0 else ""
        trace_progress(account["id"], account['details'])
    return account


async def update_task_status(id: str, details: str, order: str, status: str):
    logger.info(f"update_task_status: {id}, {details}, {order}, {status}")
    order_time = None
    if status == "success":
        order_time = get_order_time()
    try:
        await Task.filter(id=id).update(status=status, details=details, orderTime=order_time, order=order)
    except Exception as e:
        logger.error(f"update_task_status error: {e}")


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
        send_email.delay()
    else:
        asyncio.get_event_loop().run_until_complete(
            update_task_status(result['id'], result['details'], result['order'], "error"))


@celery.task()
def send_email():
    email = EmailSender()
    address = os.getenv("RECEIVED").split(",")
    username = os.getenv("EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
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


if __name__ == '__main__':
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # print(get_link(token))
