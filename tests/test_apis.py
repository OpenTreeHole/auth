import asyncio

import pytest
from aiocache import caches
from tortoise.contrib import test
from tortoise.contrib.test import finalizer, initializer

from main import app

client = AsyncClient(app=app, base_url='http://test')

from config import config, MODELS

from models import User
from utils.auth import make_identifier, totp, set_verification_code, check_verification_code
from utils.jwt_utils import decode_payload
from . import client


@pytest.fixture(scope='session', autouse=True)
def initialize_tests(request):
    initializer(MODELS, db_url=config.test_db)
    request.addfinalizer(finalizer)


cache = caches.get('default')
ACCESS_TOKEN = ''
REFRESH_TOKEN = ''
USER = User()


def generate_headers(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


class TestCommon(test.TestCase):
    async def test_home(self):
        res = await client.get('/api')
        assert res.status_code == 200
        assert res.json() == {'message': 'hello world'}

    async def test_login_required(self):
        data = {
            'email': 'test_login_required@test.com',
            'password': 'password'
        }
        user = await User.create_user(**data)
        res = await client.post('/login', json=data)
        access_token = res.json()['access']

        res = await client.get('/login_required')
        assert res.status_code == 401
        assert res.json()['message'] == 'Bearer token required'

        res = await client.get('/login_required', headers={'Authorization': f'Bearer {access_token}'})
        assert res.status_code == 200
        assert res.json()['message'] == 'you are currently logged in'
        assert res.json()['uid'] == user.id


class TestLoginLogout(test.TestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.data = {
            'email': 'TestLogin@test.com',
            'password': 'password'
        }
        await User.create_user(**self.data)

    async def test_login(self):
        res = await client.post('/login', json=self.data)
        assert res.status_code == 200
        assert 'access' in res.json()
        assert 'refresh' in res.json()

    async def test_login_wrong_password(self):
        data = self.data.copy()
        data['password'] = 'wrong password'
        res = await client.post('/login', json=data)
        assert res.status_code == 401
        assert res.json()['message'] == 'password incorrect'

    async def test_login_no_user(self):
        data = {
            'email': 'test_login_no_user@test.com',
            'password': 'password'
        }
        res = await client.post('/login', json=data)
        assert res.status_code == 404
        assert res.json()['message'] == 'User does not exist'

    async def test_logout(self):
        res = await client.post('/login', json=self.data)
        access_token = res.json()['access']

        res = await client.get('/logout', headers={'Authorization': f'Bearer {access_token}'})
        assert res.status_code == 200
        assert res.json()['message'] == 'logout successful'


class TestRefresh(test.TestCase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.data = {
            'email': 'TestRefresh@test.com',
            'password': 'password'
        }
        self.user = await User.create_user(**self.data)
        res = await client.post('/login', json=self.data)
        self.access = res.json()['access']
        self.refresh = res.json()['refresh']

    async def test_refresh(self):
        await asyncio.sleep(1)
        res = await client.post('/refresh', headers=generate_headers(self.refresh))
        assert res.status_code == 200
        access = res.json()['access']
        refresh = res.json()['refresh']
        assert refresh != self.refresh
        assert decode_payload(self.access).get('exp') < decode_payload(access).get('exp')

    async def test_wrong_refresh(self):
        res = await client.post('/refresh', headers=generate_headers(self.access))
        print(res.json())
        assert res.status_code == 401
        assert res.json()['message'] == 'refresh token invalid'


class TestRegister(test.TestCase):
    async def test_verify_with_email(self):
        data = {
            'email': 'test_verify_with_email@test.com',
            'password': 'password'
        }
        email = data['email']

        res = await client.get(f'/verify/email', params={'email': email})
        assert res.status_code == 200
        assert res.json()['message']
        assert res.json()['scope'] == 'register'
        code = await cache.get(f'register-{make_identifier(email)}')
        assert len(code) == 6
        assert isinstance(code, str)

        await User.create_user(**data)
        res = await client.get(f'/verify/email/{email}')
        assert res.status_code == 200
        assert res.json()['message']
        assert res.json()['scope'] == 'reset'
        assert await cache.get(f'reset-{make_identifier(email)}')

    async def test_verify_with_apikey(self):
        params = {
            'apikey': '123456',
            'email': 'test_verify_with_apikey@test.com',
            'check_register': False
        }
        data = {
            'email': 'test_verify_with_apikey@test.com',
            'password': 'password'
        }
        res = await client.get('/verify/apikey', params=params)
        assert res.status_code == 403
        assert res.json()['message'] == 'API Key 不正确'

        params['apikey'] = totp.now()
        res = await client.get('/verify/apikey', params=params)
        assert res.status_code == 200
        assert res.json()['message'] == '验证成功'
        assert res.json()['scope'] == 'register'
        assert res.json()['code'] == await cache.get(f'register-{make_identifier(params["email"])}')

        params['check_register'] = True
        res = await client.get('/verify/apikey', params=params)
        assert res.status_code == 200
        assert res.json()['message'] == '用户未注册'

        await User.create_user(**data)
        res = await client.get('/verify/apikey', params=params)
        assert res.status_code == 409
        assert res.json()['message'] == '用户已注册'

    async def test_register(self):
        data = {
            'email': 'test_register@test.com',
            'password': 'password',
            'verification': '123456'
        }
        res = await client.post('/register', json=data)
        assert res.status_code == 400
        assert res.json()['message'] == '验证码错误'

        code = await set_verification_code(email=data['email'], scope='register')
        data['verification'] = code
        res = await client.post('/register', json=data)
        assert res.status_code == 201
        assert res.json()['message'] == 'register successful'
        assert res.json()['access']
        assert res.json()['refresh']
        assert User.filter(identifier=make_identifier(data['email'])).exists()
        assert await check_verification_code(data['email'], code, 'register') is False

        code = await set_verification_code(email=data['email'], scope='register')
        data['verification'] = code
        res = await client.post('/register', json=data)
        assert res.status_code == 400
        assert res.json()['message'] == '该用户已注册，如果忘记密码，请使用忘记密码功能找回'

    async def test_reset_password(self):
        data = {
            'email': 'test_reset_password@test.com',
            'password': 'password',
            'verification': '123456'
        }
        res = await client.put('/register', json=data)
        assert res.status_code == 400
        assert res.json()['message'] == '验证码错误'

        code = await set_verification_code(email=data['email'], scope='reset')
        data['verification'] = code
        res = await client.put('/register', json=data)
        assert res.status_code == 404

        await User.create_user(**data)
        data['password'] = 'new password'
        res = await client.put('/register', json=data)
        assert res.status_code == 200
        assert res.json()['message'] == 'reset password successful'
        assert res.json()['access']
        assert res.json()['refresh']
        assert await check_verification_code(data['email'], code, 'register') is False
        res = await client.post('/login', json=data)
        assert res.status_code == 200
