import multiprocessing

from sanic import json, Request
from sanic.exceptions import Unauthorized, Forbidden

from settings import get_sanic_app
from utils.common import authorized, send_email
from utils.exceptions import BadRequest
from utils.validator import validate

app = get_sanic_app()

from models import User
from serializers import LoginModel, EmailModel, ApikeyVerifyModel, RegisterModel
from utils.auth import many_hashes, check_password, set_verification_code, check_api_key, check_verification_code, \
    delete_verification_code, make_password
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
    # 用户不存在，注册邮件；用户存在，重置密码
    user_exists = await User.filter(identifier=many_hashes(match.email)).exists()
    scope = 'reset' if user_exists else 'register'
    code = await set_verification_code(email=match.email, scope=scope)
    base_content = (
        f'您的验证码是: {code}\r\n'
        f'验证码的有效期为 {app.config["VERIFICATION_CODE_EXPIRES"]} 分钟\r\n'
        '如果您意外地收到了此邮件，请忽略它'
    )
    if scope == 'register':
        await send_email(
            subject=f'{app.config["SITE_NAME"]} 注册验证',
            content=f'欢迎注册 {app.config["SITE_NAME"]}，{base_content}',
            receivers=match.email
        )
    else:
        await send_email(
            subject=f'{app.config["SITE_NAME"]} 重置密码',
            content=f'您正在重置密码，{base_content}',
            receivers=match.email
        )
    return json({
        'message': '验证邮件已发送，请查收\n如未收到，请检查邮件地址是否正确，检查垃圾箱，或重试',
        'scope': scope
    })


@app.get('/verify/apikey')
@validate(query=ApikeyVerifyModel)
async def verify_with_apikey(request: Request, query: ApikeyVerifyModel):
    """
    只能注册用
    """
    scope = 'register'
    if not check_api_key(query.apikey):
        raise Forbidden('API Key 不正确')
    if await User.filter(identifier=many_hashes(query.email)).exists():
        return json({'message': '用户已注册'}, 409)
    if query.check_register:
        return json({'message': '用户未注册'})

    code = await set_verification_code(email=query.email, scope=scope)
    return json({'message': '验证成功', 'code': code, 'scope': scope})


@app.post('/register')
@validate(json=RegisterModel)
async def register(request: Request, body: RegisterModel):
    if not await check_verification_code(body.email, body.verification, 'register'):
        raise BadRequest('验证码错误')
    if await User.filter(identifier=many_hashes(body.email)).exists():
        raise BadRequest('该用户已注册，如果忘记密码，请使用忘记密码功能找回')
    user = await User.create_user(email=body.email, password=body.password)
    access_token, refresh_token = await create_tokens(user)
    await delete_verification_code(body.email, 'register')
    return json({'access': access_token, 'refresh': refresh_token, 'message': '注册成功'}, 201)


@app.put('/register')
@validate(json=RegisterModel)
async def register(request: Request, body: RegisterModel):
    """
    修改密码，重置 refresh token
    """
    if not await check_verification_code(body.email, body.verification, 'reset'):
        raise BadRequest('验证码错误')
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    user.password = make_password(body.password)
    user.save()
    access_token, refresh_token = await create_tokens(user, reset=True)
    await delete_verification_code(body.email, 'reset')
    return json({'access': access_token, 'refresh': refresh_token, 'message': '重置密码成功'}, 200)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config['DEBUG'],
        access_log=app.config['DEBUG']
    )
