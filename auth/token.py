from sanic import Request, json, Sanic, Blueprint
from sanic.exceptions import Unauthorized
from sanic_ext.extensions.openapi import openapi

from auth.response import TokensResponse, MessageResponse
from auth.serializers import LoginModel
from models import User
from utils.auth import many_hashes, check_password
from utils.common import authorized
from utils.db import get_object_or_404
from utils.jwt_utils import create_tokens
from utils.kong import delete_jwt_credentials
from utils.validator import validate

app = Sanic.get_app()
bp = Blueprint('token')


@bp.get('/login_required')
@authorized()
async def login_required(request: Request):
    return json({'message': 'you are currently logged in', 'uid': request.ctx.user.id})


@bp.post('/login')
@openapi.description('用户名密码登录')
@openapi.body(LoginModel.construct())
@openapi.response(200, TokensResponse)
@validate(json=LoginModel)
async def login(request: Request, body: LoginModel):
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    if not check_password(body.password, user.password):
        raise Unauthorized('password incorrect')
    access_token, refresh_token = await create_tokens(user)
    return json({'access': access_token, 'refresh': refresh_token})


@bp.get('/logout')
@openapi.description('单点退出，吊销 refresh token')
@openapi.secured('token')
@openapi.response(200, MessageResponse)
@authorized()
async def logout(request: Request):
    user: User = request.ctx.user
    await delete_jwt_credentials(user.id)
    return json({'message': 'logout successful'})


@bp.post('/refresh')
@openapi.description('用 refresh token 刷新 access token 和 refresh token')
@openapi.secured('token')
@openapi.response(200, TokensResponse)
@authorized(token_type='refresh')
async def refresh(request: Request):
    user: User = request.ctx.user
    access_token, refresh_token = await create_tokens(user)
    return json({'access': access_token, 'refresh': refresh_token})
