import re

from sanic import Sanic
from tortoise import fields, Tortoise
from tortoise.models import Model

from utils.auth import encrypt_email, many_hashes, make_password

app = Sanic.get_app()


class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=1000)  # RSA encrypted email
    identifier = fields.CharField(max_length=128, unique=True)  # sha3-512 of email
    password = fields.CharField(max_length=128)
    joined_time = fields.DatetimeField(auto_now_add=True)
    nickname = fields.CharField(max_length=32, default='user')

    def __str__(self):
        return f'User#{self.id}'

    @classmethod
    async def create_user(cls, email: str, password: str, **kwargs) -> 'User':
        return await cls.create(
            email=encrypt_email(email),
            identifier=many_hashes(email),
            password=make_password(password),
            **kwargs
        )


TORTOISE_ORM = {
    'apps': {
        'models': {
            'models': ['models', 'aerich.models']
        }
    },
    'use_tz': True,
    'timezone': app.config.get('TZ', 'UTC')
}
# aerich 暂不支持 sqlite
db_url = app.config.get('DB_URL', 'mysql://username:password@mysql:3306/auth')
match = re.match(r'(.+)://(.+):(.+)@(.+):(.+)/(.+)', db_url)
TORTOISE_ORM.update({'connections': {
    'default': {
        'engine': f'tortoise.backends.{match.group(1)}',
        'credentials': {
            'host': match.group(4),
            'port': match.group(5),
            'user': match.group(2),
            'password': match.group(3),
            'database': match.group(6),
        }
    },
}})


@app.signal('server.init.after')
async def init(*args, **kwargs):
    await Tortoise.init(TORTOISE_ORM)


@app.signal('server.shutdown.before')
async def close(*args, **kwargs):
    await Tortoise.close_connections()
