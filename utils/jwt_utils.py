from datetime import datetime, timezone, timedelta
from typing import Tuple

import jwt
from jwt import InvalidSignatureError, ExpiredSignatureError, DecodeError
from sanic import Sanic

from models import User
from utils.auth import get_public_key, get_private_key

app = Sanic.get_app()

JWT_PUBLIC_KEY = get_public_key(app.config.get('JWT_PUBLIC_KEY_PATH', 'data/treehole_demo_public.pem'))
JWT_PRIVATE_KEY = get_private_key(app.config.get('JWT_PRIVATE_KEY_PATH', 'data/treehole_demo_private.pem'))


def decode_payload(token: str) -> dict:
    return jwt.decode(token, options={"verify_signature": False})


def verify_token(token: str, token_type='access') -> dict:
    try:
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=['RS256'])
        if payload.get('type') != token_type:
            payload = None
    except (InvalidSignatureError, ExpiredSignatureError, DecodeError):
        payload = None
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


async def get_or_create_refresh_token(user: User) -> str:
    if verify_token(user.refresh_token, token_type='refresh'):
        return user.refresh_token

    payload = prepare_token_payload(user)
    payload['type'] = 'refresh'
    payload['exp'] = datetime.now(tz=timezone.utc) + timedelta(days=30)
    refresh_token = jwt.encode(payload, JWT_PRIVATE_KEY, algorithm='RS256')
    user.refresh_token = refresh_token
    await user.save()
    return refresh_token


async def create_tokens(user: User) -> Tuple[str, str]:
    return create_access_token(user), await get_or_create_refresh_token(user)
