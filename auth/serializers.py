from typing import Optional

from pydantic import BaseModel, validator, EmailStr, Field
from tortoise.contrib.pydantic import pydantic_model_creator

from config import config
from models import User
from utils.exceptions import ValidationError

UserSerializer = pydantic_model_creator(User)


class EmailModel(BaseModel):
    email: EmailStr

    @validator('email')
    def email_in_whitelist(cls, email):
        domain = email[email.find('@') + 1:]
        whitelist = config.email_whitelist
        if len(whitelist) > 0 and domain not in whitelist:  # 未设置 whitelist 时不检查
            raise ValidationError('email not in whitelist')
        return email


class PasswordModel(BaseModel):
    password: str = Field(min_length=8)

    # @validator('password')
    # def password_too_weak(cls, password):
    #     return password


class LoginModel(EmailModel, PasswordModel):
    pass
    """
    email, password
    """


class ApikeyVerifyModel(EmailModel):
    apikey: str
    check_register: Optional[bool] = False


class RegisterModel(LoginModel):
    """
    email, password, code
    """
    verification: str
