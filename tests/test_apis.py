import os

import pytest
from tortoise.contrib import test
from tortoise.contrib.test import finalizer, initializer

from app import app
from models import User


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["models"], db_url=db_url, app_label="models")
    request.addfinalizer(finalizer)


class TestApis(test.TestCase):
    async def test_home(self):
        req, res = await app.asgi_client.get('/')
        assert res.status == 200
        assert res.json == {'message': 'hello world'}

    async def test_login(self):
        data = {
            'email': '1@test.com',
            'password': 'password'
        }
        await User.create_user(**data)
        req, res = await app.asgi_client.post('/login', json=data)
        assert res.status == 200
        assert res.json['access']
        assert res.json['refresh']

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
