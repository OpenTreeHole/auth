from datetime import timedelta
from typing import List

import tortoise.exceptions
from fastapi import APIRouter, Depends

from admin.serializers import PermissionAdd, PermissionModel, PageModel, PermissionDelete
from models import User, Permission
from utils import kong
from utils.common import get_user, get_user_id
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
    if body.name not in to_user.roles:
        to_user.roles.append(body.name)

    # permissions with time limit
    if body.name.startswith('ban_'):
        permission = await Permission.get_or_none(user_id=user_id, name=body.name)
        # permissions that should add offense count
        to_user.offense_count += 1

        if permission:
            if permission.synced:
                # if not banned, start from now
                permission.start_time = now()
                permission.end_time = now() + timedelta(days=body.days)
                permission.synced = False
            else:
                # if is banned, accumulate
                permission.end_time += timedelta(days=body.days)

            # accumulate reasons
            permission.reason += f'\n{body.reason}'
            permission.made_by = from_user
            try:
                await permission.save()
            # reason maybe longer than 100
            except tortoise.exceptions.ValidationError:
                permission.reason = f'{body.reason}'
                await permission.save()

        else:
            await Permission.create(
                user=to_user,
                made_by=from_user,
                name=body.name,
                end_time=now() + timedelta(days=body.days),
                reason=body.reason
            )
    await to_user.save()
    log(body.name, 'ADD', to_user, from_user, body.reason)
    return {'message': 'success'}


# admin only
@router.delete('/users/{user_id}/permissions/{name}')
async def delete_permission(user_id: int, name: str, body: PermissionDelete, from_user: User = Depends(get_user)):
    to_user = await get_object_or_404(User, id=user_id)
    permission = await Permission.get_or_none(user_id=user_id, name=name)
    if permission:
        permission.synced = True
        await permission.save()

    await kong.delete_acl(user_id, name)
    try:
        to_user.roles.remove(name)
        await to_user.save()
    except ValueError:
        pass
    log(name, 'DELETE', to_user, from_user, body.reason)
    return {'message': 'success'}


# owner or admin
@router.get('/users/{user_id}/permissions', response_model=List[PermissionModel])
async def list_permissions_by_user(user_id: int, request_user_id: int = Depends(get_user_id)):
    if not request_user_id == user_id:
        raise Forbidden()
    permissions = await Permission.filter(user_id=user_id)
    return permissions


# admin only
@router.get('/permissions/{id}', response_model=PermissionModel)
async def get_permission_by_id(id: int):
    permission = await get_object_or_404(Permission, id=id)
    return permission


# admin only
@router.get('/permissions', response_model=List[PermissionModel])
async def list_permissions(query: PageModel = Depends()):
    permissions = await Permission.all().offset(query.offset).limit(query.size)
    return permissions


async def sync_permissions():
    permissions = await Permission.filter(synced=False, end_time__lt=now())
    for permission in permissions:
        await kong.delete_acl(permission.user_id, permission.name)
        permission.synced = True
        await permission.save()

        # save user status
        user = await User.get_or_none(id=permission.user_id)
        if user is not None:
            try:
                user.roles.remove(permission.name)
                await user.save()
            except ValueError:
                pass
