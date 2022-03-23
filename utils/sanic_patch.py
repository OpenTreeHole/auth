import orjson
import sanic
from sanic import HTTPResponse


def dumps_str(*args, **kwargs) -> str:
    return orjson.dumps(*args, **kwargs).decode('utf-8')


def json(data, *args) -> HTTPResponse:
    if isinstance(data, str):
        return sanic.json(data, *args, dumps=lambda x: x)
    else:
        return sanic.json(data, *args, dumps=dumps_str)
