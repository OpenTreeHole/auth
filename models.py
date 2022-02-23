from sanic import Sanic
from tortoise import fields
from tortoise.models import Model

from utils.auth import rsa_encrypt, many_hashes, make_password, create_token

app = Sanic.get_app()


class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=1000)  # RSA encrypted email
    identifier = fields.CharField(max_length=128, unique=True)  # sha3-512 of email
    password = fields.CharField(max_length=128)
    refresh_token = fields.CharField(max_length=2000, default='')
    joined_time = fields.DatetimeField(auto_now_add=True)
    nickname = fields.CharField(max_length=32, default='user')

    def __str__(self):
        return f'User#{self.id}'

    @classmethod
    async def create_user(cls, email: str, password: str, **kwargs) -> 'User':
        user = await cls.create(
            email=rsa_encrypt(email),
            identifier=many_hashes(email),
            password=make_password(password),
            **kwargs
        )
        _, refresh_token = create_token(user.id)
        user.refresh_token = refresh_token
        await user.save()
        return user
