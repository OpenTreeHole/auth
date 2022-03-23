from datetime import datetime

from sanic import Sanic

app = Sanic.get_app()


def now():
    return datetime.now(app.config['TZ'])
