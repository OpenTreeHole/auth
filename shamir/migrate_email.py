import asyncio

from tortoise import Tortoise

import config
from gpg import encrypt_email
from models import User
from utils.auth import rsa_decrypt


async def migrate_email():
    for user in (await User.all()):
        email = rsa_decrypt(user.email)
        await encrypt_email(email, user.id)
        print(user.id)


async def main():
    await Tortoise.init(config=config.TORTOISE_ORM)

    await migrate_email()

    await Tortoise.close_connections()


if __name__ == '__main__':
    asyncio.run(main())
