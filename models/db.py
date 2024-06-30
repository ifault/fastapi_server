from tortoise import fields
from tortoise.models import Model
import uuid

class User(Model):
    id = fields.TextField(pk=True, default=str(uuid.uuid4))
    username = fields.TextField()
    password = fields.TextField()

    class Meta:
        table = 'User'


class History(Model):
    id = fields.IntField(pk=True, generated=True)
    username = fields.TextField(null=False)
    targetDay = fields.TextField(null=True)
    order = fields.TextField(null=True)
    orderTime = fields.TextField(null=True)

    class Meta:
        table = 'History'


class Task(Model):
    id = fields.TextField(pk=True, default=str(uuid.uuid4))
    taskId = fields.TextField(null=True)
    username = fields.TextField(null=False)
    password = fields.TextField(null=False)
    category = fields.TextField(null=False)
    order = fields.TextField(null=True)
    cardNumber = fields.TextField(null=True)  # 假设 cardNumber 可以为 NULL
    count = fields.IntField(null=True)
    targetDay = fields.TextField(null=True)  # 假设 targetDay 可以为 NULL
    status = fields.TextField(null=True)  # 假设 status 可以为 NULL
    userId = fields.TextField(null=False)
    details = fields.TextField(null=True)  # 假设 details 可以为 NULL
    orderTime = fields.TextField(null=True)  # 假设 orderTime 可以为 NULL
    cardCount = fields.IntField(default=0)
    scheduleTime = fields.TextField(null=True)  #

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
