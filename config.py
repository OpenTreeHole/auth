import os
from datetime import tzinfo
from typing import List

import pytz
from aiocache import Cache
from fastapi.openapi.utils import get_openapi
from pydantic import BaseSettings, Field
from pytz import UnknownTimeZoneError
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

cache = Cache()


def default_debug() -> bool:
    return os.getenv('MODE', 'dev') != 'production'


def parse_tz() -> tzinfo:
    try:
        return pytz.timezone(os.getenv('TZ', 'Asia/Shanghai'))
    except UnknownTimeZoneError:
        return pytz.UTC


class Settings(BaseSettings):
    mode: str = 'dev'
    debug: bool = Field(default_factory=default_debug)
    tz: tzinfo = pytz.UTC
    db_url: str = 'sqlite://db.sqlite3'
    test_db: str = 'sqlite://:memory:'
    default_size: int = 10
    site_name: str = 'Open Tree Hole'
    email_whitelist: List[str] = []
    verification_code_expires: int = 10
    email_user: str = ''
    email_password: str = ''
    email_host: str = ''
    email_port: int = 465
    email_use_tls: bool = True
    email_public_key_path: str = 'data/treehole_demo_public.pem'
    email_private_key_path: str = 'data/treehole_demo_private.pem'
    register_apikey_seed: str = ''
    kong_url: str = 'http://kong:8001'
    kong_token: str = ''
    authorize_in_debug: bool = True


config = Settings(tz=parse_tz())
print(config.tz)
if config.mode != 'production':
    print(f'server is running in {config.mode} mode, do not use in production')
if not config.email_whitelist:
    print(f'email whitelist not set')

TORTOISE_ORM = {
    'apps': {
        'models': {
            'models': ['models', 'aerich.models']
        }
    },
    'connections': {  # aerich 暂不支持 sqlite
        'default': config.db_url
    },
    'use_tz': True,
    'timezone': str(config.tz)
}
from main import app

import models

if config.mode != 'test':
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
Tortoise.init_models([models], 'models')


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title='OpenTreeHole Docs',
        version="2.0.0",
        description="OpenAPI doc for OpenTreeHole",
        routes=app.routes
    )

    # look for the error 422 and removes it
    for path in openapi_schema['paths'].values():
        for method in path:
            try:
                del path[method]['responses']['422']
            except KeyError:
                pass

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
