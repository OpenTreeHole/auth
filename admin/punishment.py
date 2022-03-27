from datetime import timedelta
from typing import List

from dateutil.parser import isoparse
from fastapi import APIRouter, Request, Depends

from admin.serializers import PunishmentAdd, PunishmentModel, PunishmentList, PageModel
from models import User, Punishment
from utils.common import get_user
from utils.exceptions import Forbidden
from utils.orm import get_object_or_404, serialize
from utils.values import now

router = APIRouter(tags=['punishment'])


@router.post('/users/{user_id}/punishments', response_model=PunishmentModel)
async def add_punishment(user_id: int, body: PunishmentAdd, from_user: User = Depends(get_user)):
    to_user = await get_object_or_404(User, id=user_id)
    end_time = now() + timedelta(days=body.days)
    punishment = await Punishment.create(
        user=to_user,
        made_by=from_user,
        scope=body.scope,
        end_time=end_time,
        reason=body.reason
    )
    if body.scope not in to_user.silent:
        to_user.silent[body.scope] = end_time
    else:
        to_user.silent[body.scope] = max(
            isoparse(to_user.silent[body.scope]),
            end_time
        )
    to_user.offense_count += 1
    await to_user.save()
    return (await PunishmentModel.from_tortoise_orm(punishment)).dict()


@router.get('/users/{user_id}/punishments', response_model=List[PunishmentModel])
async def list_punishments_by_user(user_id: int, user: User = Depends(get_user)):
    if not user.id == user_id and not user.is_admin:
        raise Forbidden()
    punishments = Punishment.filter(user_id=user_id)
    return await serialize(punishments, PunishmentList)


@router.get('/users/{user_id}/punishments/{id}', response_model=PunishmentModel)
async def get_punishment_by_user(user_id: int, id: int, user: User = Depends(get_user)):
    if not user.id == user_id and not user.is_admin:
        raise Forbidden()
    punishment = await get_object_or_404(Punishment, id=id)
    return await serialize(punishment, PunishmentModel)


@router.get('/punishments/{id}', response_model=PunishmentModel)
async def get_punishment_by_id(id: int, user: User = Depends(get_user)):
    if not user.is_admin:
        raise Forbidden()
    punishment = await get_object_or_404(Punishment, id=id)
    return await serialize(punishment, PunishmentModel)


@router.get('/punishments', response_model=PunishmentModel)
async def list_punishments(request: Request, query: PageModel = Depends(), user: User = Depends(get_user)):
    if not user.is_admin:
        raise Forbidden()
    punishments = Punishment.all().offset(query.offset).limit(query.size)
    return await serialize(punishments, PunishmentList)
