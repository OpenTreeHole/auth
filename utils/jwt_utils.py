from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional

import jwt
from jwt import DecodeError

from models import User
from utils.kong import get_jwt_credential, JwtCredential, get_acls
from utils.orm import serialize, models_creator
from utils.values import now


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


def create_refresh_token(payload: dict, credential: JwtCredential) -> str:
    payload['type'] = 'refresh'
    payload['exp'] = payload['iat'] + timedelta(days=30)
    return jwt.encode(payload, credential.secret, algorithm=credential.algorithm)


JWTUser, _ = models_creator(User, exclude=('joined_time', 'last_login'))


async def create_tokens(user: User) -> Tuple[str, str]:
    """
    Args:
        user: User

    Returns:
        access_token, refresh_token

    """
    user.last_login = now()
    user.roles = await get_acls(user.id)
    await user.save()

    credential = await get_jwt_credential(user.id)
    payload = {
        'uid': user.id,
        'iss': credential.key,
        'iat': datetime.now(tz=timezone.utc),
    }
    payload.update(await serialize(user, JWTUser))

    return create_access_token(payload, credential), create_refresh_token(payload, credential)
