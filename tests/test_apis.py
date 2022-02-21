import os

import pytest
from sanic_testing import TestManager
from tortoise.contrib import test
from tortoise.contrib.test import finalizer, initializer

from app import app as server


@pytest.yield_fixture
def app():
    TestManager(server)
    yield server


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["models"], db_url=db_url, app_label="models")
    request.addfinalizer(finalizer)


class TestApis(test.TestCase):
    async def test_home(self, app):
        req, res = await app.asgi_client.get('/')
        assert res.status == 200
        assert res.json == {'message': 'hello world'}

    async def test_login(self, app):
        req, res = await app.asgi_client.post('/login', json={
            'email': 'email@email.com',
            'password': 'password'
        })
        assert res.status == 404
