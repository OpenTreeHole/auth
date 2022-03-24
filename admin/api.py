from datetime import timedelta

from dateutil.parser import isoparse
from sanic import Blueprint, Request
from sanic.exceptions import Forbidden
from sanic_ext.extensions.openapi import openapi

from admin.serializers import PunishmentAdd, PunishmentModel, PunishmentList
from models import User, Punishment
from utils.common import authorized
from utils.orm import get_object_or_404, serialize
from utils.sanic_patch import json
from utils.validator import validate
from utils.values import now

bp = Blueprint('admin')


@bp.post('/users/<user_id:int>/punishments')
@openapi.response(200, PunishmentModel.construct())
@openapi.body(PunishmentAdd)
@authorized()
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
    return json((await PunishmentModel.from_tortoise_orm(punishment)).dict())


@bp.get('/users/<user_id:int>/punishments')
@openapi.response(200, PunishmentList.construct())
@authorized()
async def list_punishments_by_user(request: Request, user_id: int):
    if not request.ctx.user.id == user_id and not request.ctx.user.is_admin:
        raise Forbidden()
    punishments = Punishment.all()
    return json(await serialize(punishments, PunishmentList))


@bp.get('/users/<user_id:int>/punishments/<id:int>')
@openapi.response(200, PunishmentModel.construct())
@authorized()
async def get_punishment_by_user(request: Request, user_id: int, id: int):
    if not request.ctx.user.id == user_id and not request.ctx.user.is_admin:
        raise Forbidden()
    punishment = await get_object_or_404(Punishment, id=id)
    return json(await serialize(punishment, PunishmentModel))
