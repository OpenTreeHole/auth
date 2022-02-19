from sanic import json, Sanic
from sanic.exceptions import Unauthorized
from sanic_ext import validate

from models import User
from serializers import LoginSerializer
from utils.auth import many_hashes, check_password
from utils.db import get_object_or_404

app = Sanic.get_app()


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
