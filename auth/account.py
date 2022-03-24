from sanic import Request, json, Blueprint, Sanic
from sanic.exceptions import Forbidden
from sanic_ext.extensions.openapi import openapi

from auth.response import EmailVerifyResponse, APIKeyVerifyResponse, TokensResponse
from auth.serializers import EmailModel, ApikeyVerifyModel, RegisterModel
from models import User
from utils.auth import many_hashes, set_verification_code, check_api_key, check_verification_code, \
    delete_verification_code, make_password
from utils.common import send_email
from utils.exceptions import BadRequest
from utils.jwt_utils import create_tokens
from utils.kong import delete_jwt_credentials
from utils.orm import get_object_or_404
from utils.validator import validate

app = Sanic.get_app()
bp = Blueprint('account')


@bp.get('/verify/email/<email:str>')
@openapi.description('邮箱验证\n用户不存在，注册邮件；用户存在，重置密码')
@openapi.response(200, EmailVerifyResponse)
@validate(match=EmailModel)
async def verify_with_email(request: Request, match: EmailModel, **kwargs):
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


@bp.get('/verify/email')
@openapi.description('邮箱验证\n用户不存在，注册邮件；用户存在，重置密码')
@openapi.response(200, EmailVerifyResponse)
@validate(query=EmailModel)
async def verify_with_email(request: Request, query: EmailModel, **kwargs):
    user_exists = await User.filter(identifier=many_hashes(query.email)).exists()
    scope = 'reset' if user_exists else 'register'
    code = await set_verification_code(email=query.email, scope=scope)
    base_content = (
        f'您的验证码是: {code}\r\n'
        f'验证码的有效期为 {app.config["VERIFICATION_CODE_EXPIRES"]} 分钟\r\n'
        '如果您意外地收到了此邮件，请忽略它'
    )
    if scope == 'register':
        await send_email(
            subject=f'{app.config["SITE_NAME"]} 注册验证',
            content=f'欢迎注册 {app.config["SITE_NAME"]}，{base_content}',
            receivers=query.email
        )
    else:
        await send_email(
            subject=f'{app.config["SITE_NAME"]} 重置密码',
            content=f'您正在重置密码，{base_content}',
            receivers=query.email
        )
    return json({
        'message': '验证邮件已发送，请查收\n如未收到，请检查邮件地址是否正确，检查垃圾箱，或重试',
        'scope': scope
    })


@bp.get('/verify/apikey')
@openapi.description('APIKey验证\n只能注册用')
@openapi.parameter('email', str)
@openapi.parameter('apikey', str)
@openapi.response(200, APIKeyVerifyResponse)
@validate(query=ApikeyVerifyModel)
async def verify_with_apikey(request: Request, query: ApikeyVerifyModel):
    scope = 'register'
    if not check_api_key(query.apikey):
        raise Forbidden('API Key 不正确')
    if await User.filter(identifier=many_hashes(query.email)).exists():
        return json({'message': '用户已注册'}, 409)
    if query.check_register:
        return json({'message': '用户未注册'})

    code = await set_verification_code(email=query.email, scope=scope)
    return json({'message': '验证成功', 'code': code, 'scope': scope})


@bp.post('/register')
@openapi.description('用户注册')
@openapi.body(RegisterModel)
@openapi.response(200, TokensResponse)
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


@bp.put('/register')
@openapi.description('修改密码')
@openapi.body(RegisterModel)
@openapi.response(200, TokensResponse)
@validate(json=RegisterModel)
async def change_password(request: Request, body: RegisterModel):
    """
    修改密码，重置 refresh token
    """
    if not await check_verification_code(body.email, body.verification, 'reset'):
        raise BadRequest('验证码错误')
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    user.password = make_password(body.password)
    await user.save()
    await delete_jwt_credentials(user.id)
    access_token, refresh_token = await create_tokens(user)
    await delete_verification_code(body.email, 'reset')
    return json({'access': access_token, 'refresh': refresh_token, 'message': '重置密码成功'}, 200)
