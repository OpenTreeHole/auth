import asyncio
import os

import pytest
from tortoise.contrib import test
from tortoise.contrib.test import finalizer, initializer

from app import app
from models import User
from settings import cache
from utils.auth import many_hashes
from utils.jwt_utils import decode_payload


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["models"], db_url=db_url, app_label="models")
    request.addfinalizer(finalizer)


ACCESS_TOKEN = ''
REFRESH_TOKEN = ''
USER = User()


class TestSetUp(test.TestCase):
    @pytest.mark.run(order=1)
    async def test_set_up(self):
        """
        没用，好像不同的类用的数据库不一样
        """
        global ACCESS_TOKEN
        global REFRESH_TOKEN
        global USER

        data = {
            'email': 'test@test.com',
            'password': 'password'
        }
        USER = await User.create_user(**data)
        req, res = await app.asgi_client.post('/login', json=data)
        ACCESS_TOKEN = res.json['access']
        REFRESH_TOKEN = res.json['refresh']


class TestCommon(test.TestCase):
    async def test_home(self):
        req, res = await app.asgi_client.get('/')
        assert res.status == 200
        assert res.json == {'message': 'hello world'}

    async def test_login_required(self):
        data = {
            'email': 'test_login_required@test.com',
            'password': 'password'
        }
        user = await User.create_user(**data)
        req, res = await app.asgi_client.post('/login', json=data)
        access_token = res.json['access']

        req, res = await app.asgi_client.get('/login_required')
        assert res.status == 401
        assert res.json['message'] == 'access token invalid'

        req, res = await app.asgi_client.get('/login_required', headers={'Authorization': f'Bearer {access_token}'})
        assert res.status == 200
        assert res.json['message'] == 'you are currently logged in'
        assert res.json['uid'] == user.id


class TestLogin(test.TestCase):
    async def test_login(self):
        data = {
            'email': '1@test.com',
            'password': 'password'
        }
        await User.create_user(**data)
        req, res = await app.asgi_client.post('/login', json=data)
        assert res.status == 200
        assert 'access' in res.json
        assert 'refresh' in res.json

    async def test_login_wrong_password(self):
        data = {
            'email': '2@test.com',
            'password': 'password'
        }
        await User.create_user(**data)
        data['password'] = 'wrong password'
        req, res = await app.asgi_client.post('/login', json=data)
        assert res.status == 401
        assert res.json['message'] == 'password incorrect'

    async def test_login_no_user(self):
        data = {
            'email': '3@test.com',
            'password': 'password'
        }
        req, res = await app.asgi_client.post('/login', json=data)
        assert res.status == 404
        assert res.json['message'] == 'User does not exist'


class TestLogout(test.TestCase):
    async def test_logout(self):
        data = {
            'email': 'test_logout@test.com',
            'password': 'password'
        }
        user = await User.create_user(**data)
        req, res = await app.asgi_client.post('/login', json=data)
        access_token = res.json['access']

        req, res = await app.asgi_client.get('/logout', headers={'Authorization': f'Bearer {access_token}'})
        assert res.status == 200
        assert res.json['message'] == 'logout successful'
        user = await User.get(id=user.id)
        assert user.refresh_token == ''


class TestRefresh(test.TestCase):
    async def test_refresh(self):
        data = {
            'email': '4@test.com',
            'password': 'password'
        }
        await User.create_user(**data)
        req, res = await app.asgi_client.post('/login', json=data)
        old_access = res.json['access']
        old_refresh = res.json['refresh']
        await asyncio.sleep(1)
        req, res = await app.asgi_client.post('/refresh', headers={'Authorization': f'Bearer {old_refresh}'})
        assert res.status == 200
        access = res.json['access']
        refresh = res.json['refresh']
        assert refresh == old_refresh
        assert decode_payload(old_access).get('exp') < decode_payload(access).get('exp')

    async def test_wrong_refresh(self):
        req, res = await app.asgi_client.post('/refresh')
        assert res.status == 401
        assert res.json['message'] == 'refresh token invalid'


class TestRegister(test.TestCase):
    async def test_verify(self):
        data = {
            'email': 'testverify@test.com',
            'password': 'password'
        }
        email = data['email']
        key = many_hashes(email)

        req, res = await app.asgi_client.get(f'/verify/email/{email}')
        assert res.status == 200
        assert res.json['message']
        assert res.json['type'] == 'register'
        code = await cache.get(key)
        assert len(code) == 6
        assert isinstance(code, str)

        await User.create_user(**data)
        req, res = await app.asgi_client.get(f'/verify/email/{email}')
        assert res.status == 200
        assert res.json['message']
        assert res.json['type'] == 'reset'
        assert await cache.get(key) != code
