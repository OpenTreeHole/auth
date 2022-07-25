import asyncio

from tortoise import Tortoise

import config
from gpg import encrypt_email
from models import User, RegisteredEmail
from utils.auth import rsa_decrypt, make_identifier


async def run():
    for user in (await User.all()):
        email = rsa_decrypt(user.email)
        user.identifier = make_identifier(email)
        await asyncio.gather(
            encrypt_email(email, user.id),
            RegisteredEmail.add(email)
        )
        print(user.id)


async def main():
    await Tortoise.init(config=config.TORTOISE_ORM)

    await run()

    await Tortoise.close_connections()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
