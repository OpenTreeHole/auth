import multiprocessing

from sanic import json, Request
from sanic.exceptions import Unauthorized

from settings import get_sanic_app
from utils.common import authorized
from utils.validator import validate

app = get_sanic_app()

from models import User
from serializers import LoginModel, EmailModel
from utils.auth import many_hashes, check_password
from utils.jwt_utils import create_tokens
from utils.db import get_object_or_404


@app.middleware('request')
async def add_token(request: Request):
    """
    获取 token 而不作检测
    """
    authorization = request.headers.get('authorization', 'Bearer ')
    request.ctx.token = authorization[7:].strip()


@app.get('/')
async def home(request: Request):
    return json({'message': 'hello world'})


@app.get('/login_required')
@authorized()
async def login_required(request: Request):
    return json({'message': 'you are currently logged in', 'uid': request.ctx.user.id})


@app.post('/login')
@validate(json=LoginModel)
async def login(request: Request, body: LoginModel):
    """
    用户名密码登录，返回 access token 和 refresh token
    """
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    if not check_password(body.password, user.password):
        raise Unauthorized('password incorrect')
    access_token, refresh_token = await create_tokens(user)
    return json({'access': access_token, 'refresh': refresh_token})


@app.get('/logout')
@authorized()
async def logout(request: Request):
    """
    单点退出，吊销 refresh token
    """
    user: User = request.ctx.user
    user.refresh_token = ''
    await user.save()
    return json({'message': 'logout successful'})


@app.post('/refresh')
@authorized(token_type='refresh')
async def refresh(request: Request):
    """
    header 里面带 refresh token，返回 access token 和 refresh token
    """
    user: User = request.ctx.user
    access_token, refresh_token = await create_tokens(user)
    return json({'access': access_token, 'refresh': refresh_token})


@app.get('/verify/email/<email:str>')
@validate(match=EmailModel)
async def verify_with_email(request: Request, match: EmailModel, **kwargs):
    return json({'message': match.email})


@app.post('/register')
async def register(request: Request):
    return json({})


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config['DEBUG'],
        access_log=app.config['DEBUG']
    )
