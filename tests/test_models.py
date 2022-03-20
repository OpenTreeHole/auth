from tortoise.contrib import test
from tortoise.contrib.pydantic import pydantic_model_creator

import app
from models.db import User

print(app)


class TestModels(test.TestCase):
    async def test_create_user(self):
        user = await User.create_user(email='email', password='password')
        p = await pydantic_model_creator(User).from_tortoise_orm(user)
