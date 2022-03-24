from datetime import datetime

from sanic import Sanic

app = Sanic.get_app()

DEFAULT_SIZE = 10


def now():
    return datetime.now(app.config['TZ'])
