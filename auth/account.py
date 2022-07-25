from fastapi import APIRouter, Depends
from pydantic import ValidationError
from starlette.responses import JSONResponse

from auth.response import EmailVerifyResponse, APIKeyVerifyResponse, TokensResponse
from auth.serializers import EmailModel, ApikeyVerifyModel, RegisterModel, LoginModel
from config import config
from models import User, RegisteredEmail, DeletedEmail
from utils.auth import make_identifier, set_verification_code, check_api_key, check_verification_code, \
    delete_verification_code, make_password, check_password
from utils.common import send_email, get_user
from utils.exceptions import BadRequest, Forbidden
from utils.jwt_utils import create_tokens
from utils.kong import delete_jwt_credentials
from utils.orm import get_object_or_404

router = APIRouter(tags=['account'])


async def _verify_with_email(email: str) -> dict:
    registered = await RegisteredEmail.has_email(email)
    scope = 'reset' if registered else 'register'
    code = await set_verification_code(email=email, scope=scope)
    base_content = (
        f'您的验证码是: {code}\r\n'
        f'验证码的有效期为 {config.verification_code_expires} 分钟\r\n'
        '如果您意外地收到了此邮件，请忽略它'
    )
    if scope == 'register':
        await send_email(
            subject=f'{config.site_name} 注册验证',
            content=f'欢迎注册 {config.site_name}，{base_content}',
            receivers=email
        )
    else:
        await send_email(
            subject=f'{config.site_name} 重置密码',
            content=f'您正在重置密码，{base_content}',
            receivers=email
        )
    return {
        'message': '验证邮件已发送，请查收\n如未收到，请检查邮件地址是否正确，检查垃圾箱，或重试',
        'scope': scope
    }


@router.get('/verify/email/{email}', deprecated=True, response_model=EmailVerifyResponse)
async def verify_with_email_old(email: str):
    try:
        match = EmailModel(email=email)
    except ValidationError:
        raise BadRequest('email invalid')
    return _verify_with_email(match.email)


@router.get('/verify/email', response_model=EmailVerifyResponse)
async def verify_with_email(query: EmailModel = Depends()):
    return _verify_with_email(query.email)


@router.get('/verify/apikey', response_model=APIKeyVerifyResponse)
async def verify_with_apikey(query: ApikeyVerifyModel = Depends()):
    scope = 'register'
    if not check_api_key(query.apikey):
        raise Forbidden('API Key 不正确')
    if await RegisteredEmail.has_email(query.email):
        return JSONResponse({'message': '用户已注册'}, 409)
    if query.check_register:
        return JSONResponse({'message': '用户未注册'}, 200)

    code = await set_verification_code(email=query.email, scope=scope)
    return {'message': '验证成功', 'code': code, 'scope': scope}


@router.post('/register', response_model=TokensResponse, status_code=201)
async def register(body: RegisterModel):
    if not await check_verification_code(body.email, body.verification, 'register'):
        raise BadRequest('验证码错误')
    registered = await RegisteredEmail.has_email(body.email)
    deleted = await DeletedEmail.has_email(body.email)
    if registered:
        if not deleted:
            raise BadRequest('该用户已注册，如果忘记密码，请使用忘记密码功能找回')
        else:
            user = await User.all_objects.filter(identifier=make_identifier(body.email)).first()
            user.is_active = True
            user.password = make_password(body.password)
            await user.save()
    else:
        user = await User.create_user(email=body.email, password=body.password)
    access_token, refresh_token = await create_tokens(user)
    await delete_verification_code(body.email, 'register')
    return {'access': access_token, 'refresh': refresh_token, 'message': 'register successful'}


@router.put('/register', response_model=TokensResponse)
async def change_password(body: RegisterModel):
    """
    修改密码，重置 refresh token
    """
    if not await check_verification_code(body.email, body.verification, 'reset'):
        raise BadRequest('验证码错误')
    user = await get_object_or_404(User, identifier=make_identifier(body.email))
    user.password = make_password(body.password)
    await user.save()
    await delete_jwt_credentials(user.id)
    access_token, refresh_token = await create_tokens(user)
    await delete_verification_code(body.email, 'reset')
    return {'access': access_token, 'refresh': refresh_token, 'message': 'reset password successful'}


@router.delete('/users/me', status_code=204)
async def delete_user(body: LoginModel, user: User = Depends(get_user)):
    # TODO: safe password
    if not check_password(body.password, user.password):
        raise Forbidden('password incorrect')
    # TODO: verify email
    await user.delete_user(body.email)
    return None
