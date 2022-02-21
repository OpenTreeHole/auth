import multiprocessing

from sanic import Sanic, json

app = Sanic('auth')
from sanic.exceptions import Unauthorized
from sanic.log import logger
from sanic_ext import validate

from models import User
from serializers import LoginSerializer
from utils.auth import many_hashes, check_password
from utils.db import get_object_or_404

if app.config.get('DEBUG', True):
    logger.warning('\nserver is running in dev mode, do not use in production\n')


@app.get('/')
async def home(request):
    return json({'message': 'hello world'})


@app.post('/login')
@validate(json=LoginSerializer)
async def login(request, body: LoginSerializer):
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    if not check_password(body.password, user.password):
        raise Unauthorized('password incorrect')
    return json({'login': True})


@app.post('/register')
async def register(request):
    return json({})


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config.get('DEBUG', True),
        access_log=app.config.get('ACCESS_LOG', True)
    )
