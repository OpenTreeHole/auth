import re

from pydantic import BaseModel, validator
from sanic import Sanic
from tortoise.contrib.pydantic import pydantic_model_creator

from models import User
from utils.exceptions import ValidationError

app = Sanic.get_app()

# serialize object
# user = await UserSerializer.from_tortoise_orm(user)
# return json(user.json(), dumps=lambda x: x)
UserSerializer = pydantic_model_creator(User)


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
        if len(whitelist) > 0 and domain not in whitelist:  # 未设置 whitelist 时不检查
            raise ValidationError('email not in whitelist')
        return email

    @validator('password')
    def password_too_weak(cls, password):
        if len(password) < 8:
            raise ValidationError('password too weak')
        return password


class RefreshSerializer(BaseModel):
    token: str
