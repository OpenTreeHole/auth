from typing import Optional

from pydantic import BaseModel

from config import config
from models import Permission, User
from utils.orm import models_creator

PermissionModel, PermissionList = models_creator(Permission)
_UserModel, UserList = models_creator(User)


class UserModel(_UserModel):
    permission: dict
    user_id: int
    favorites: list[int]


class PermissionDelete(BaseModel):
    reason: Optional[str] = ''


class PermissionAdd(PermissionDelete):
    days: Optional[int] = 1
    name: str


class PageModel(BaseModel):
    size: Optional[int] = config.default_size
    offset: Optional[int] = 0


class UserGet(PageModel):
    role: Optional[str]


class UserModify(BaseModel):
    nickname: Optional[str]
