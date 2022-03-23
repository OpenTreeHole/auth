from typing import Optional

from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from models import Punishment

PunishT = pydantic_model_creator(Punishment)


class PunishmentAdd(BaseModel):
    reason: Optional[str] = ''
    days: Optional[int] = 1
    scope: str
