import base64
import os
import re
from datetime import tzinfo
from typing import List, Optional

import pytz
from aiocache import caches
from fastapi.openapi.utils import get_openapi
from pydantic import BaseSettings, Field
from pytz import UnknownTimeZoneError
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise


def default_debug() -> bool:
    return os.getenv('MODE', 'dev') != 'production'


def parse_tz() -> tzinfo:
    try:
        return pytz.timezone(os.getenv('TZ', 'Asia/Shanghai'))
    except UnknownTimeZoneError:
        return pytz.UTC


def get_secret(name: str) -> Optional[str]:
    """
    The function to get variables from docker secrets
    :param name: the name of the docker secret
    :return: the secret value after type cast
    """
    try:
        with open(os.path.join('/var/run/secrets', name), 'r', encoding='utf-8') as secret_file:
            value = secret_file.read().rstrip('\n')
    except Exception as e:
        print(e)
        return

    return value


class Settings(BaseSettings):
    mode: str = 'dev'
    debug: bool = Field(default_factory=default_debug)
    tz: tzinfo = pytz.UTC
    db_url: str = 'sqlite://db.sqlite3'
    test_db: str = 'sqlite://:memory:'
    default_size: int = 10
    site_name: str = 'Open Tree Hole'
    domain: str = 'fduhole.com'
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
    redis_url: str = 'redis://redis:6379'
    identifier_salt: str = str(base64.b64encode(b'123456'), 'utf-8')
    provision_key: str = ''


config = Settings(tz=parse_tz())

SECRET_FIELDS = [
    'db_url',
    'email_password',
    'register_apikey_seed',
    'identifier_salt',
    'provision_key',
    'kong_token'
]
for name in SECRET_FIELDS:
    value = get_secret(name)
    if value:
        setattr(config, name, value)

if not config.debug:
    match = re.match(r'redis://(.+):(\d+)', config.redis_url)
    assert match
    caches.set_config({
        'default': {
            'cache': 'aiocache.RedisCache',
            'endpoint': match.group(1),
            'port': match.group(2),
            'timeout': 5
        }})
else:
    caches.set_config({
        'default': {
            'cache': 'aiocache.SimpleMemoryCache'
        }})

if config.mode != 'production':
    print(f'server is running in {config.mode} mode, do not use in production')
if not config.email_whitelist:
    print(f'email whitelist not set')

MODELS = ['models', 'shamir']

TORTOISE_ORM = {
    'apps': {
        'models': {
            'models': ['aerich.models'] + MODELS
        }
    },
    'connections': {  # aerich 暂不支持 sqlite
        'default': config.db_url
    },
    'use_tz': True,
    'timezone': 'utc'
}
from main import app

if config.mode != 'test':
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )

Tortoise.init_models(MODELS, 'models')


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
