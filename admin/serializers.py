from typing import Optional

from pydantic import BaseModel

from models import Punishment
from utils.orm import models_creator
from utils.values import DEFAULT_SIZE

PunishmentModel, PunishmentList = models_creator(Punishment)


class PunishmentAdd(BaseModel):
    reason: Optional[str] = ''
    days: Optional[int] = 1
    scope: str


class PageModel(BaseModel):
    size: Optional[int] = DEFAULT_SIZE
    offset: Optional[int] = 0
