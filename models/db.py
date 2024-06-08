import uuid

from tortoise import fields
from tortoise.models import Model
import datetime


class Users(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255, unique=True, index=True)
    password = fields.CharField(max_length=255, index=True, default=str(uuid.uuid4().hex))
    expired = fields.DatetimeField(default=datetime.datetime.now() + datetime.timedelta(days=30))
    created_at = fields.DatetimeField(auto_now_add=True)
    access_token = fields.TextField(max_length=255, null=True)


class Accounts(Model):
    uuid = fields.CharField(pk=True, max_length=50)
    username = fields.CharField(max_length=50)
    password = fields.CharField(max_length=50)
    order = fields.TextField(null=True, default="")
    details = fields.TextField(null=True, default="")
    status = fields.TextField(default="free")
    task_id = fields.TextField(null=True, default="")
    order_time = fields.DatetimeField(null=True)
    user = fields.ForeignKeyField('models.Users', related_name='accounts')


class Paid(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255)
    order_str = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    user = fields.ForeignKeyField('models.Users', related_name='paid')


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.TextField()
    password = fields.TextField()


class History(Model):
    id = fields.IntField(pk=True, generated=True)
    username = fields.TextField(null=False)
    targetDay = fields.TextField(null=True)
    order = fields.TextField(null=True)
    orderTime = fields.TextField(null=True)
    class Meta:
        table = 'History'

class Task(Model):
    id = fields.IntField(pk=True, generated=True)
    taskId = fields.TextField(null=True)
    username = fields.TextField(null=False)
    password = fields.TextField(null=False)
    category = fields.TextField(null=False)
    order = fields.TextField(null=True)
    cardNumber = fields.TextField(null=True)  # 假设 cardNumber 可以为 NULL
    count = fields.IntField()
    targetDay = fields.TextField(null=True)  # 假设 targetDay 可以为 NULL
    status = fields.TextField(null=True)  # 假设 status 可以为 NULL
    userId = fields.IntField(null=False)
    details = fields.TextField(null=True)  # 假设 details 可以为 NULL
    orderTime = fields.TextField(null=True)  # 假设 orderTime 可以为 NULL

    class Meta:
        table = 'Task'

    def to_dict(self):
        return {
            "id": self.id,
            "taskId": self.taskId,
            "username": self.username,
            "password": self.password,
            "category": self.category,
            "cardNumber": self.cardNumber,
            "count": self.count,
            "targetDay": self.targetDay,
            "status": self.status,
            "userId": self.userId,
            "orderTime": self.orderTime,
            "details": self.details,
            "order": self.order
        }
