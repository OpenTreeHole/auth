import re

from sanic import Sanic
from sanic.log import logger
from tortoise import Tortoise

app = Sanic('auth')
app.config['MODE'] = MODE = app.config.get('MODE', 'dev')
app.config['DEBUG'] = (app.config['MODE'] != 'production')

if MODE != 'production':
    logger.warning(f'\nserver is running in {MODE} mode, do not use in production\n')

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


@app.signal('server.init.after')
async def init(*args, **kwargs):
    if MODE != 'test':
        await Tortoise.init(TORTOISE_ORM)


@app.signal('server.shutdown.before')
async def close(*args, **kwargs):
    if MODE != 'test':
        await Tortoise.close_connections()


def get_sanic_app():
    return app
