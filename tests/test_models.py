import os

import pytest
from tortoise.contrib import test
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.contrib.test import finalizer, initializer

import app
from models import User

print(app)


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(["models"], db_url=db_url, app_label="models")
    request.addfinalizer(finalizer)


class TestModels(test.TestCase):
    async def test_create_user(self):
        user = await User.create_user(email='email', password='password')
        p = await pydantic_model_creator(User).from_tortoise_orm(user)
        print(p.json(indent=4))
