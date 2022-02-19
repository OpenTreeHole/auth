import re

from pydantic import BaseModel, validator
from sanic import Sanic

from utils.exceptions import ValidationError

app = Sanic.get_app()


class LoginSerializer(BaseModel):
    email: str
    password: str

    @validator('email')
    def email_in_whitelist(cls, email):
        match = re.match(r'.+@(.+\..+)', email)
        if not match:
            raise ValidationError('invalid email format')
        domain = match.group(1)
        whitelist = app.config.get('EMAIL_WHITELIST', [])
        if whitelist and domain not in whitelist:  # 未设置 whitelist 时不检查
            raise ValidationError('email not in whitelist')
        return email

    @validator('password')
    def password_too_weak(cls, password):
        if len(password) < 8:
            raise ValidationError('password too weak')
        return password
