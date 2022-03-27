from fastapi import APIRouter, Depends
from pydantic import ValidationError
from starlette.responses import JSONResponse

from auth.response import EmailVerifyResponse, APIKeyVerifyResponse, TokensResponse
from auth.serializers import EmailModel, ApikeyVerifyModel, RegisterModel
from config import config
from models import User
from utils.auth import many_hashes, set_verification_code, check_api_key, check_verification_code, \
    delete_verification_code, make_password
from utils.common import send_email
from utils.exceptions import BadRequest, Forbidden
from utils.jwt_utils import create_tokens
from utils.kong import delete_jwt_credentials
from utils.orm import get_object_or_404

router = APIRouter(tags=['account'])


@router.get('/verify/email/{email}', deprecated=True, response_model=EmailVerifyResponse)
async def verify_with_email_old(email: str):
    try:
        match = EmailModel(email=email)
    except ValidationError:
        raise BadRequest('email invalid')
    user_exists = await User.filter(identifier=many_hashes(match.email)).exists()
    scope = 'reset' if user_exists else 'register'
    code = await set_verification_code(email=match.email, scope=scope)
    base_content = (
        f'您的验证码是: {code}\r\n'
        f'验证码的有效期为 {config.verification_code_expires} 分钟\r\n'
        '如果您意外地收到了此邮件，请忽略它'
    )
    if scope == 'register':
        await send_email(
            subject=f'{config.site_name} 注册验证',
            content=f'欢迎注册 {config.site_name}，{base_content}',
            receivers=match.email
        )
    else:
        await send_email(
            subject=f'{config.site_name} 重置密码',
            content=f'您正在重置密码，{base_content}',
            receivers=match.email
        )
    return {
        'message': '验证邮件已发送，请查收\n如未收到，请检查邮件地址是否正确，检查垃圾箱，或重试',
        'scope': scope
    }


@router.get('/verify/email', response_model=EmailVerifyResponse)
async def verify_with_email(query: EmailModel = Depends()):
    user_exists = await User.filter(identifier=many_hashes(query.email)).exists()
    scope = 'reset' if user_exists else 'register'
    code = await set_verification_code(email=query.email, scope=scope)
    base_content = (
        f'您的验证码是: {code}\r\n'
        f'验证码的有效期为 {config.verification_code_expires} 分钟\r\n'
        '如果您意外地收到了此邮件，请忽略它'
    )
    if scope == 'register':
        await send_email(
            subject=f'{config.site_name} 注册验证',
            content=f'欢迎注册 {config.site_name}，{base_content}',
            receivers=query.email
        )
    else:
        await send_email(
            subject=f'{config.site_name} 重置密码',
            content=f'您正在重置密码，{base_content}',
            receivers=query.email
        )
    return {
        'message': '验证邮件已发送，请查收\n如未收到，请检查邮件地址是否正确，检查垃圾箱，或重试',
        'scope': scope
    }


@router.get('/verify/apikey', response_model=APIKeyVerifyResponse)
async def verify_with_apikey(query: ApikeyVerifyModel = Depends()):
    scope = 'register'
    if not check_api_key(query.apikey):
        raise Forbidden('API Key 不正确')
    if await User.filter(identifier=many_hashes(query.email)).exists():
        return JSONResponse({'message': '用户已注册'}, 409)
    if query.check_register:
        return JSONResponse({'message': '用户未注册'}, 200)

    code = await set_verification_code(email=query.email, scope=scope)
    return {'message': '验证成功', 'code': code, 'scope': scope}


@router.post('/register', response_model=TokensResponse, status_code=201)
async def register(body: RegisterModel):
    if not await check_verification_code(body.email, body.verification, 'register'):
        raise BadRequest('验证码错误')
    user = await User.all_objects.filter(identifier=many_hashes(body.email)).first()
    if user:
        if user.is_active:
            raise BadRequest('该用户已注册，如果忘记密码，请使用忘记密码功能找回')
        else:  # 可能为已删除的用户
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
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    user.password = make_password(body.password)
    await user.save()
    await delete_jwt_credentials(user.id)
    access_token, refresh_token = await create_tokens(user)
    await delete_verification_code(body.email, 'reset')
    return {'access': access_token, 'refresh': refresh_token, 'message': 'reset password successful'}
