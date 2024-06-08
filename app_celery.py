from celery import Celery
from celery.schedules import timedelta


def create_app():
    celery_ = Celery(
        __name__,
        broker='redis://172.18.0.1:6379/0',
        backend="db+postgresql://user:pass@host.docker.internal:5432/db",
        task_ignore_result=False,
        include=['tasks.morning']
    )
    return celery_


celery = create_app()
celery.conf.update(
    CELERYBEAT_SCHEDULE={
        'run-every-5-seconds-for-run': {
            'task': 'tasks.morning.run_task',
            'schedule': timedelta(seconds=5),
            'args': []
        },
        'run-every-5-seconds-for-stop': {
            'task': 'tasks.morning.stop_task',
            'schedule': timedelta(seconds=5),
            'args': []
        },
    },
)
