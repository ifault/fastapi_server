import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()


def create_app():
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("DATABASE_PORT")
    name = os.getenv("DATABASE_NAME")
    user = os.getenv("DATABASE_USER")
    pass_ = os.getenv("DATABASE_PASSWORD")
    r_host = os.getenv("REDIS_HOST")
    r_port = os.getenv("REDIS_PORT")
    celery_ = Celery(
        __name__,
        broker=f'redis://{r_host}:{r_port}/0',
        backend=F"db+postgresql://{user}:{pass_}@{host}:{port}/{name}",
        task_ignore_result=False,
        include=['tasks.morning']
    )
    return celery_


celery = create_app()
# celery.conf.update(
#     CELERYBEAT_SCHEDULE={
#     },
# )
