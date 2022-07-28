import asyncio

from aerich import Command

from config import TORTOISE_ORM


async def migrate():
    command = Command(tortoise_config=TORTOISE_ORM)
    await command.init()
    print(await command.migrate())
    print(await command.upgrade())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(migrate())
