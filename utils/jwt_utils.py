from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional

import jwt
from jwt import DecodeError
from sanic import Sanic

from models import User
from utils.kong import get_jwt_credential, JwtCredential

app = Sanic.get_app()


def decode_payload(token: str) -> Optional[dict]:
    """
    校验 token，仅解码 payload
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except DecodeError:
        return


def verify_token(token: str, token_type='access') -> Optional[dict]:
    """
    连接 API 网关查询 token 是否有效
    """
    pass


def create_access_token(payload: dict, credential: JwtCredential) -> str:
    payload['type'] = 'access'
    payload['exp'] = payload['iat'] + timedelta(minutes=30)
    return jwt.encode(payload, credential.secret, algorithm=credential.algorithm)


async def create_refresh_token(payload: dict, credential: JwtCredential) -> str:
    payload['type'] = 'refresh'
    payload['exp'] = payload['iat'] + timedelta(days=30)
    refresh_token = jwt.encode(payload, credential.secret, algorithm=credential.algorithm)
    return refresh_token


async def create_tokens(user: User) -> Tuple[str, str]:
    """
    Args:
        user: User

    Returns:
        access_token, refresh_token

    """
    credential = await get_jwt_credential(user.id)
    payload = {
        'uid': user.id,
        'iss': credential.key,
        'iat': datetime.now(tz=timezone.utc)
    }
    return create_access_token(payload, credential), await create_refresh_token(payload, credential)
