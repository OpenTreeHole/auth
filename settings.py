import json
import re
from json import JSONDecodeError

from aiocache import Cache
from sanic import Sanic
from sanic.log import logger
from tortoise import Tortoise


# 环境变量可以解析 int，bool，无法解析数组
def parse_array(s: str) -> list:
    try:
        return json.loads(s)
    except JSONDecodeError:
        return []


app = Sanic('auth')
app.config['MODE'] = MODE = app.config.get('MODE', 'dev')
app.config['DEBUG'] = (app.config['MODE'] != 'production')
app.config['SITE_NAME'] = app.config.get('SITE_NAME', 'Open Tree Hole')
app.config['EMAIL_WHITELIST'] = parse_array(app.config.get('EMAIL_WHITELIST', ''))
app.config['VERIFICATION_CODE_EXPIRES'] = app.config.get('VERIFICATION_CODE_EXPIRES', 5)

TORTOISE_ORM = {
    'apps': {
        'models': {
            'models': ['models', 'aerich.models']
        }
    },
    'use_tz': True,
    'timezone': app.config.get('TZ', 'UTC')
}
db_url = app.config.get('DB_URL', 'mysql://username:password@mysql:3306/auth')
match = re.match(r'(.+)://(.+):(.+)@(.+):(.+)/(.+)', db_url)
# aerich 暂不支持 sqlite
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

if MODE != 'production':
    logger.warning(f'server is running in {MODE} mode, do not use in production')
if not app.config['EMAIL_WHITELIST']:
    logger.warning(f'email whitelist not set')


@app.signal('server.init.after')
async def init(*args, **kwargs):
    if MODE != 'test':
        await Tortoise.init(TORTOISE_ORM)


@app.signal('server.shutdown.before')
async def close(*args, **kwargs):
    if MODE != 'test':
        await Tortoise.close_connections()


cache = Cache()


def get_sanic_app() -> Sanic:
    return app
