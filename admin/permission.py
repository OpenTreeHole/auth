from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends

from admin.serializers import PermissionAdd, PermissionModel, PageModel, PermissionDelete
from models import User, Permission
from utils import kong
from utils.common import get_user
from utils.exceptions import Forbidden
from utils.orm import get_object_or_404
from utils.values import now

router = APIRouter(tags=['permission'])


def log(name: str, action: str, to: User, by: User, reason: str):
    print(f'permission {name} {action} to {to} by {by} because of {reason}')


# admin only
@router.post('/users/{user_id}/permissions')
async def add_permission(user_id: int, body: PermissionAdd, from_user: User = Depends(get_user)):
    to_user = await get_object_or_404(User, id=user_id)
    await kong.add_acl(user_id, body.name)
    log(body.name, 'ADD', to_user, from_user, body.reason)

    # permissions with time limit
    if body.name.startswith('ban_'):
        permission = await Permission.get_or_none(user_id=user_id, name=body.name)

        if permission:
            permission.end_time += timedelta(days=body.days)
            permission.reason += f'\n{body.reason}'
            await permission.save()
        else:
            await Permission.create(
                user=to_user,
                made_by=from_user,
                name=body.name,
                end_time=now() + timedelta(days=body.days),
                reason=body.reason
            )

    # permissions that should add offense count
    if body.name.startswith('ban_'):
        to_user.offense_count += 1
        await to_user.save()

    return {'message': 'success'}


# admin only
@router.delete('/users/{user_id}/permissions/{name}')
async def delete_permission(user_id: int, name: str, body: PermissionDelete, from_user: User = Depends(get_user)):
    to_user = await get_object_or_404(User, id=user_id)
    await kong.delete_acl(user_id, name)
    log(name, 'DELETE', to_user, from_user, body.reason)
    return {'message': 'success'}


# owner or admin
@router.get('/users/{user_id}/permissions', response_model=List[PermissionModel])
async def list_permissions_by_user(user_id: int, user: User = Depends(get_user)):
    if not user.id == user_id:
        raise Forbidden()
    permissions = await Permission.filter(user_id=user_id)
    return permissions


# admin only
@router.get('/permissions/{id}', response_model=PermissionModel)
async def get_permission_by_id(id: int):
    permission = await get_object_or_404(Permission, id=id)
    return permission


# admin only
@router.get('/permissions', response_model=PermissionModel)
async def list_permissions(query: PageModel = Depends()):
    permissions = Permission.all().offset(query.offset).limit(query.size)
    return permissions


async def sync_permissions():
    permissions = await Permission.filter(synced=False, end_time__lt=now())
    for permission in permissions:
        await kong.delete_acl(permission.user_id, permission.name)
        permission.synced = True
        await permission.save()
