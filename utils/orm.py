from typing import Type, Tuple, Union

from sanic.exceptions import NotFound
from tortoise import Model
from tortoise.contrib.pydantic import PydanticModel, PydanticListModel, pydantic_model_creator, \
    pydantic_queryset_creator
from tortoise.queryset import MODEL, QuerySet


def models_creator(cls: Type[Model], **kwargs) -> Tuple[Type[PydanticModel], Type[PydanticListModel]]:
    return pydantic_model_creator(cls, **kwargs), pydantic_queryset_creator(cls, **kwargs)


async def get_object_or_404(cls: Type[MODEL], *args, **kwargs) -> MODEL:
    instance = await cls.get_or_none(*args, **kwargs)
    if not instance:
        raise NotFound(f'{cls.__name__} does not exist')
    return instance


async def exists_or_404(cls: Type[MODEL], *args, **kwargs) -> bool:
    if not await cls.filter(*args, **kwargs).exists():
        raise NotFound(f'{cls.__name__} does not exist')
    return True


async def serialize(obj: Union[MODEL, QuerySet], cls: Union[PydanticModel, PydanticListModel]) -> dict:
    if isinstance(obj, Model):
        return (await cls.from_tortoise_orm(obj)).dict()
    elif isinstance(obj, QuerySet):
        model = await cls.from_queryset(obj)
        return model.dict()['__root__']
