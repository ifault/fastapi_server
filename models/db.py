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
