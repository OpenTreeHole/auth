from typing import List

from fastapi import APIRouter
from fastapi.params import Depends

from admin.serializers import UserModel, PageModel, UserList, UserModify
from auth.serializers import PasswordModel
from models import User
from utils.auth import check_password
from utils.common import get_user
from utils.exceptions import Forbidden
from utils.kong import delete_jwt_credentials
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


@router.put('/users/{user_id}', response_model=UserModel)
async def modify_user(user_id: int, body: UserModify, from_user: User = Depends(get_user)):
    if not from_user.is_admin:
        raise Forbidden()
    user = await get_object_or_404(User, id=user_id)
    user = await user.update_from_dict(body.dict())
    await user.save()
    return await serialize(user, UserModel)


@router.delete('/users/me', status_code=204)
async def delete_user(body: PasswordModel, user: User = Depends(get_user)):
    if not check_password(body.password, user.password):
        raise Forbidden('password incorrect')
    user.is_active = False
    await user.save()
    await delete_jwt_credentials(user.id)
    return None
