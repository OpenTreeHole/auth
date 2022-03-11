from typing import Optional

from pydantic import BaseModel, validator, EmailStr
from sanic import Sanic
from tortoise.contrib.pydantic import pydantic_model_creator

from models import User
from utils.exceptions import ValidationError

app = Sanic.get_app()

# serialize object
# user = await UserSerializer.from_tortoise_orm(user)
# return json(user.json(), dumps=lambda x: x)
UserSerializer = pydantic_model_creator(User)


class EmailModel(BaseModel):
    email: EmailStr

    @validator('email')
    def email_in_whitelist(cls, email):
        domain = email[email.find('@') + 1:]
        whitelist = app.config.get('EMAIL_WHITELIST', [])
        if len(whitelist) > 0 and domain not in whitelist:  # 未设置 whitelist 时不检查
            raise ValidationError('email not in whitelist')
        return email


class LoginModel(EmailModel):
    """
    email, password
    """
    password: str

    @validator('password')
    def password_too_weak(cls, password):
        if len(password) < 8:
            raise ValidationError('password too weak')
        return password


class ApikeyVerifyModel(EmailModel):
    apikey: str
    check_register: Optional[bool] = False


class RegisterModel(LoginModel):
    """
    email, password, code
    """
    verification: str
