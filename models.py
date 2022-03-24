from sanic import Sanic
from tortoise import fields
from tortoise.models import Model

from utils import kong
from utils.auth import rsa_encrypt, many_hashes, make_password

app = Sanic.get_app()


class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=1000)  # RSA encrypted email
    identifier = fields.CharField(max_length=128, unique=True)  # sha3-512 of email
    password = fields.CharField(max_length=128)
    joined_time = fields.DatetimeField(auto_now_add=True)
    nickname = fields.CharField(max_length=32, default='user')
    is_admin = fields.BooleanField(default=False)
    silent = fields.JSONField(default=dict)
    offense_count = fields.IntField(default=0)
    punishments: fields.ReverseRelation['Punishment']
    punishments_made: fields.ReverseRelation['Punishment']

    def __str__(self):
        return f'User#{self.id}'

    class PydanticMeta:
        # include = ['id', 'joined_time', 'nickname', 'is_admin', 'silent', 'offense_count']
        include = ['id']
        allow_cycles = False
        max_recursion = 1

    @classmethod
    async def create_user(cls, email: str, password: str, **kwargs) -> 'User':
        user = await cls.create(
            email=rsa_encrypt(email),
            identifier=many_hashes(email),
            password=make_password(password),
            **kwargs
        )
        await kong.create_user(user.id)
        return user

    # def is_silenced(self, division_id):
    #     now = datetime.now(app.config['TZ'])
    #     division = str(division_id)  # JSON 序列化会将字典的 int 索引转换成 str
    #     if not self.silenced.get(division):  # 未设置禁言，返回 False
    #         return False
    #     else:
    #         expire_time = parser.isoparse(self.silenced.get(division))
    #         return expire_time > now


class Punishment(Model):
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField('models.User', related_name='punishments')
    made_by: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField('models.User', related_name='punishments_made')
    reason = fields.CharField(max_length=100, default='')
    scope = fields.CharField(max_length=32, default='default')
    start_time = fields.DatetimeField(auto_now_add=True)
    end_time = fields.DatetimeField(auto_now_add=True)

    class PydanticMeta:
        exclude = []
        allow_cycles = False
        max_recursion = 1