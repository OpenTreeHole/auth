import time
from functools import wraps
from inspect import isawaitable

from sanic.exceptions import Unauthorized

from models import User
from utils.db import get_object_or_404
from utils.jwt_utils import verify_refresh_token, verify_token


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
        async def decorated_function(request, *args, **kwargs):
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
