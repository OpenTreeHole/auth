from sanic.exceptions import NotFound


async def get_object_or_404(klass, *args, **kwargs):
    instance = await klass.get_or_none(*args, **kwargs)
    if not instance:
        raise NotFound(f'{klass.__name__} does not exist')
    return instance
