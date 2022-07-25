from typing import Optional

from pydantic import BaseModel

from config import config
from models import Permission, User
from utils.orm import models_creator

PermissionModel, PermissionList = models_creator(Permission)
UserModel, UserList = models_creator(
    User,
    include=('joined_time', 'nickname', 'is_admin', 'silent', 'offense_count')
)


class PermissionDelete(BaseModel):
    reason: Optional[str] = ''


class PermissionAdd(PermissionDelete):
    days: Optional[int] = 1
    name: str


class PageModel(BaseModel):
    size: Optional[int] = config.default_size
    offset: Optional[int] = 0


class UserModify(BaseModel):
    nickname: Optional[str]
