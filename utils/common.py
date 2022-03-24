import time
from email.message import EmailMessage
from functools import wraps
from inspect import isawaitable
from typing import Union, List

import aiosmtplib
from sanic import Request, Sanic
from sanic.exceptions import Unauthorized

from models import User
from utils.db import get_object_or_404
from utils.jwt_utils import decode_payload

app = Sanic.get_app()


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f'{func.__name__} consumed {(end - start) * 1000} ms')

    return wrapper


async def _authorize(request: Request, token_type) -> User:
    if app.config['DEBUG']:
        user = await User.get_or_none(id=1)
        if not user:
            user = await User.create_user(email='', password='')
        return user
    payload = decode_payload(request.ctx.token)
    if not payload or payload.get('type') != token_type and not app.config['DEBUG']:
        raise Unauthorized(f'{token_type} token invalid', scheme='Bearer')
    return await get_object_or_404(User, id=payload.get('uid'))


def authorized(token_type='access'):
    """
    位于 API 网关之后，认为 token 已校验，仅检查 token type
    """

    def decorator(f):
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            request.ctx.user = await _authorize(request, token_type)
            response = f(request, *args, **kwargs)
            if isawaitable(response):
                response = await response

            return response

        return decorated_function

    return decorator


async def send_email(subject: str, content: str, receivers: Union[List[str], str]) -> bool:
    message = EmailMessage()
    message['From'] = app.config.get('EMAIL_USER', '')
    message['To'] = ','.join(receivers) if isinstance(receivers, list) else receivers
    message["Subject"] = subject
    message.set_content(content)

    if app.config['DEBUG']:
        for i in message.items():
            print(f'{i[0]}: {i[1]}')
        print('\n', message.get_content())
        return True

    await aiosmtplib.send(
        message,
        hostname=app.config.get('EMAIL_HOST', ''),
        port=app.config.get('EMAIL_PORT', 465),
        username=app.config.get('EMAIL_USER', ''),
        password=app.config.get('EMAIL_PASSWORD', ''),
        use_tls=app.config.get('EMAIL_TLS', True)
    )
    return True
