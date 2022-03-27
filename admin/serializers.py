from typing import Optional

from pydantic import BaseModel

from config import config
from models import Punishment, User
from utils.orm import models_creator

PunishmentModel, PunishmentList = models_creator(Punishment)
UserModel, UserList = models_creator(
    User,
    include=('joined_time', 'nickname', 'is_admin', 'silent', 'offense_count')
)


class PunishmentAdd(BaseModel):
    reason: Optional[str] = ''
    days: Optional[int] = 1
    scope: str


class PageModel(BaseModel):
    size: Optional[int] = config.default_size
    offset: Optional[int] = 0
