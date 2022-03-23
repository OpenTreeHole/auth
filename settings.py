import json
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
app.config.OAS_UI_DEFAULT = 'swagger'
app.ext.openapi.add_security_scheme(
    "token",
    "http",
    scheme="bearer",
    bearer_format="JWT",
)
app.config.FALLBACK_ERROR_FORMAT = 'json'

TORTOISE_ORM = {
    'apps': {
        'models': {
            'models': ['models', 'aerich.models']
        }
    },
    'connections': {  # aerich 暂不支持 sqlite
        'default': app.config.get('DB_URL', 'mysql://username:password@mysql:3306/auth')
    },
    'use_tz': True,
    'timezone': app.config.get('TZ', 'UTC')
}

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
