from typing import List

from fastapi import APIRouter
from fastapi.params import Depends

from admin.serializers import UserModel, PageModel, UserList
from models import User
from utils.common import get_user
from utils.exceptions import Forbidden
from utils.orm import get_object_or_404, serialize

router = APIRouter(tags=['user'])


@router.get('/users/me', response_model=UserModel)
async def get_current_user(user: User = Depends(get_user)):
    return await serialize(user, UserModel)


@router.get('/users/{user_id}', response_model=UserModel)
async def get_user_by_id(user_id: int, user: User = Depends(get_user)):
    if not user.id == user_id and not user.is_admin:
        raise Forbidden()
    user = await get_object_or_404(User, id=user_id)
    return await serialize(user, UserModel)


@router.get('/users', response_model=List[UserModel])
async def list_users(query: PageModel = Depends(), user: User = Depends(get_user)):
    if not user.is_admin:
        raise Forbidden()
    users = User.all().offset(query.offset).limit(query.size)
    return await serialize(users, UserList)
