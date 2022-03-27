from email.message import EmailMessage
from typing import Union, List, Optional

import aiosmtplib
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import config
from models import User
from utils.exceptions import Unauthorized
from utils.jwt_utils import decode_payload
from utils.orm import get_object_or_404

token_scheme = HTTPBearer(auto_error=False)


class JWTValidator:
    def __init__(self, token_type: str = 'access'):
        self.token_type = token_type
        self.debug = False

    async def __call__(self, token: Optional[HTTPAuthorizationCredentials] = Depends(token_scheme)):
        if config.debug and self.debug:
            user = await User.get_or_none(id=1)
            if not user:
                user = await User.create_user(email='', password='')
            return user
        if not token:
            raise Unauthorized('Bearer token required')
        payload = decode_payload(token.credentials)
        if not payload or payload.get('type') != self.token_type:
            raise Unauthorized(f'{self.token_type} token invalid')
        return await get_object_or_404(User, id=payload.get('uid'))


get_user = JWTValidator()
get_user_by_refresh_token = JWTValidator(token_type='refresh')


async def send_email(subject: str, content: str, receivers: Union[List[str], str]) -> bool:
    message = EmailMessage()
    message['From'] = config.email_user
    message['To'] = ','.join(receivers) if isinstance(receivers, list) else receivers
    message["Subject"] = subject
    message.set_content(content)

    if config.debug:
        for i in message.items():
            print(f'{i[0]}: {i[1]}')
        print('\n', message.get_content())
        return True

    await aiosmtplib.send(
        message,
        hostname=config.email_host,
        port=config.email_port,
        username=config.email_user,
        password=config.email_password,
        use_tls=config.email_use_tls
    )
    return True
