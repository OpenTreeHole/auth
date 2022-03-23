from datetime import timedelta

from dateutil.parser import isoparse
from sanic import Blueprint, Request
from sanic_ext.extensions.openapi import openapi

from admin.serializers import PunishmentAdd, PunishT
from models import User, Punishment
from utils.db import get_object_or_404
from utils.sanic_patch import json
from utils.validator import validate
from utils.values import now

bp = Blueprint('admin')


@bp.post('/users/<user_id:int>/punishments')
@openapi.response(200, PunishT.construct())
@openapi.body(PunishmentAdd)
@validate(json=PunishmentAdd)
async def add_punishment(request: Request, user_id: int, body: PunishmentAdd):
    user = await get_object_or_404(User, id=user_id)
    end_time = now() + timedelta(days=body.days)
    punishment = await Punishment.create(
        user=user,
        made_by=request.ctx.user,
        scope=body.scope,
        end_time=end_time,
        reason=body.reason
    )
    if body.scope not in user.silent:
        user.silent[body.scope] = end_time
    else:
        user.silent[body.scope] = max(
            isoparse(user.silent[body.scope]),
            end_time
        )
    user.offense_count += 1
    await user.save()
    return json(PunishT.from_tortoise_orm(punishment).dict())
