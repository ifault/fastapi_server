from celery import Celery
from sqlalchemy import create_engine


def create_app():
    celery_ = Celery(
        __name__,
        broker='redis://redis:6379/0',
        backend="db+postgresql://user:pass@postgres:5432/db",
        task_ignore_result=False,
        include=['tasks.morning']
    )
    return celery_


celery = create_app()
