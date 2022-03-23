from typing import Type

from sanic.exceptions import NotFound
from tortoise.models import MODEL


async def get_object_or_404(cls: Type[MODEL], *args, **kwargs) -> MODEL:
    instance = await cls.get_or_none(*args, **kwargs)
    if not instance:
        raise NotFound(f'{cls.__name__} does not exist')
    return instance
