from sanic import Blueprint, Request
from sanic.exceptions import Forbidden

from admin.serializers import UserModel, PageModel, UserList
from models import User
from utils import myopenapi
from utils.common import authorized
from utils.orm import get_object_or_404, serialize
from utils.sanic_patch import json
from utils.validator import validate

bp = Blueprint('user')


@bp.get('/users/me')
@myopenapi.response(200, UserModel.construct())
@authorized()
async def get_current_user(request: Request):
    return json(await serialize(request.ctx.user, UserModel))


@bp.get('/users/<user_id:int>')
@myopenapi.response(200, UserModel.construct())
@authorized()
async def get_user_by_id(request: Request, user_id: int):
    if not request.ctx.user.id == user_id and not request.ctx.user.is_admin:
        raise Forbidden()
    user = await get_object_or_404(User, id=user_id)
    return json(await serialize(user, UserModel))


@bp.get('/users')
@myopenapi.response(200, [UserModel.construct()])
@myopenapi.query(PageModel)
@validate(query=PageModel)
@authorized()
async def list_users(request: Request, query: PageModel):
    if not request.ctx.user.is_admin:
        raise Forbidden()
    users = User.all().offset(query.offset).limit(query.size)
    return json(await serialize(users, UserList))
