import secrets
import time
from email.message import EmailMessage
from functools import wraps
from inspect import isawaitable
from typing import Union, List

import aiosmtplib
from sanic import Request, Sanic
from sanic.exceptions import Unauthorized

from models import User
from settings import cache
from utils.auth import many_hashes
from utils.db import get_object_or_404
from utils.jwt_utils import verify_refresh_token, verify_token

app = Sanic.get_app()


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f'{func.__name__} consumed {(end - start) * 1000} ms')

    return wrapper


def authorized(token_type='access'):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            if token_type == 'access':
                payload = verify_token(request.ctx.token)
            else:
                payload = await verify_refresh_token(request.ctx.token)
            if not payload:
                raise Unauthorized(f'{token_type} token invalid', scheme='Bearer')

            request.ctx.user = await get_object_or_404(User, id=payload.get('uid'))
            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

            return response

        return decorated_function

    return decorator


async def set_verification_code(email: str) -> str:
    """
    缓存中设置验证码，key 为 hashed
    """
    code = str(secrets.randbelow(1000000)).zfill(6)
    await cache.set(
        key=many_hashes(email),
        value=code,
        ttl=app.config.get('VERIFICATION_CODE_EXPIRES', 5) * 60
    )
    return code


async def send_email(title: str, content: str, receivers: Union[List[str], str]):
    message = EmailMessage()
    message['From'] = app.config.get('EMAIL_USER', '')
    message['To'] = ','.join(receivers) if isinstance(receivers, list) else receivers
    message["Subject"] = title
    message.set_content(content)

    await aiosmtplib.send(
        message,
        hostname=app.config.get('EMAIL_HOST', ''),
        port=app.config.get('EMAIL_PORT', 465),
        username=app.config.get('EMAIL_USER', ''),
        password=app.config.get('EMAIL_PASSWORD', ''),
        use_tls=app.config.get('EMAIL_TLS', True)
    )
