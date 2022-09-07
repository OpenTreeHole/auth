from typing import List

from fastapi import APIRouter
from fastapi.params import Depends

from admin.serializers import UserModel, UserModify, UserGet
from models import User
from utils.common import get_user
from utils.exceptions import Forbidden
from utils.orm import get_object_or_404

router = APIRouter(tags=['user'])


@router.get('/users/me', response_model=UserModel)
async def get_current_user(user: User = Depends(get_user)):
    return preprocess(user)


# owner or admin
@router.get('/users/{user_id}', response_model=UserModel)
async def get_user_by_id(user_id: int, user: User = Depends(get_user)):
    if not user.id == user_id:
        raise Forbidden()
    user = await get_object_or_404(User, id=user_id)
    return preprocess(user)


# admin only
@router.get('/users', response_model=List[UserModel])
async def list_users(query: UserGet = Depends()):
    if query.role:
        queryset = User.filter(roles__contains=[query.role])
    else:
        queryset = User.all()
    if query.size != 0:
        queryset = queryset.limit(query.size)
    queryset = queryset.offset(query.offset)

    users = await queryset
    return preprocess_many(users)


# admin only
@router.put('/users/{user_id}', response_model=UserModel)
async def modify_user(user_id: int, body: UserModify):
    user = await get_object_or_404(User, id=user_id)
    user = await user.update_from_dict(body.dict())
    await user.save()
    return preprocess(user)


def preprocess(user: User) -> User:
    user.user_id = user.id
    user.favorites = []
    if not user.config:
        user.config = {}

    user.permission = {'silent': {}}
    if 'admin' in user.roles:
        user.permission['admin'] = '9999-01-01T00:00:00+00:00'
    else:
        user.permission['admin'] = '1970-01-01T00:00:00+00:00'

    return user


def preprocess_many(users: list[User]) -> list[User]:
    for user in users:
        preprocess(user)
    return users
