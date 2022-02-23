import multiprocessing

from sanic import json
from sanic.exceptions import Unauthorized
from sanic_ext import validate

from settings import get_sanic_app

app = get_sanic_app()

from models import User
from serializers import LoginSerializer
from utils.auth import many_hashes, check_password, create_token
from utils.db import get_object_or_404


@app.get('/')
async def home(request):
    return json({'message': 'hello world'})


@app.post('/login')
@validate(json=LoginSerializer)
async def login(request, body: LoginSerializer):
    user = await get_object_or_404(User, identifier=many_hashes(body.email))
    if not check_password(body.password, user.password):
        raise Unauthorized('password incorrect')
    access_token, refresh_token = create_token(user.id)
    user.refresh_token = refresh_token
    await user.save()
    return json({'access': access_token, 'refresh': refresh_token})


@app.post('/register')
async def register(request):
    return json({})


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config['DEBUG'],
        access_log=app.config['DEBUG']
    )
