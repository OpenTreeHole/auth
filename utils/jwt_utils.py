from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional

import jwt
from jwt import InvalidSignatureError, ExpiredSignatureError, DecodeError
from sanic import Sanic

from models import User
from utils.auth import get_public_key, get_private_key
from utils.db import get_object_or_404

app = Sanic.get_app()

JWT_PUBLIC_KEY = get_public_key(app.config.get('JWT_PUBLIC_KEY_PATH', 'data/treehole_demo_public.pem'))
JWT_PRIVATE_KEY = get_private_key(app.config.get('JWT_PRIVATE_KEY_PATH', 'data/treehole_demo_private.pem'))


def decode_payload(token: str) -> dict:
    """
    校验 token，仅解码 payload
    """
    return jwt.decode(token, options={"verify_signature": False})


def verify_token(token: str, token_type='access') -> Optional[dict]:
    """
    仅校验 token 本身，不连接数据库
    """
    try:
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
        if payload.get('type') != token_type:
            payload = None
    except (InvalidSignatureError, ExpiredSignatureError, DecodeError):
        payload = None
    return payload


async def verify_refresh_token(token: str) -> Optional[dict]:
    """
    校验 token 并确保与数据库中的 token 相同
    """
    payload = verify_token(token, token_type='refresh')
    if not payload:
        return
    user = await get_object_or_404(User, id=payload.get('uid'))
    if user.refresh_token != token:
        return
    return payload


def prepare_token_payload(user: User) -> dict:
    return {
        'uid': user.id,
        'iss': app.config.get('SITE_NAME', ''),
        'iat': datetime.now(tz=timezone.utc)
    }


def create_access_token(user: User) -> str:
    payload = prepare_token_payload(user)
    payload['type'] = 'access'
    payload['exp'] = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm='RS256')


async def create_refresh_token(user: User) -> str:
    """
    也会更新数据库中的 token
    """
    payload = prepare_token_payload(user)
    payload['type'] = 'refresh'
    payload['exp'] = datetime.now(tz=timezone.utc) + timedelta(days=30)
    refresh_token = jwt.encode(payload, JWT_PRIVATE_KEY, algorithm='RS256')
    user.refresh_token = refresh_token
    await user.save()
    return refresh_token


async def get_or_create_refresh_token(user: User) -> str:
    if verify_token(user.refresh_token, token_type='refresh'):
        return user.refresh_token
    return await create_refresh_token(user)


async def create_tokens(user: User, reset=False) -> Tuple[str, str]:
    """
    Args:
        user: User
        reset: 重置 refresh token

    Returns:
        access_token, refresh_token

    """
    if reset:
        return create_access_token(user), await create_refresh_token(user)
    return create_access_token(user), await get_or_create_refresh_token(user)
