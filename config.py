import os
import re
from datetime import tzinfo
from typing import List

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


def get_secret(name: str, default=None, d_type: callable = str,
               secrets_dir: str = os.path.join(os.path.abspath(os.sep), 'var', 'run', 'secrets')):
    """
    The function to get variables from docker secrets
    :param name: the name of the docker secret
    :param default: the default value of the variable
    :param d_type: the type to cast to
    :param secrets_dir: the directory stores the secrets
    :return: the secret value after type cast
    """
    try:
        with open(os.path.join(secrets_dir, name), 'r') as secret_file:
            value = secret_file.read().rstrip('\n')
        if value is None:
            value = default
    except IOError as e:
        raise e

    try:
        if value is None:
            raise TypeError('Cannot get secret variable {}'.format(name))
        return d_type(value)
    except TypeError as e:
        raise e


class Settings(BaseSettings):
    mode: str = 'dev'
    debug: bool = Field(default_factory=default_debug)
    tz: tzinfo = pytz.UTC
    db_url: str = get_secret('db_url', 'sqlite://db.sqlite3', str)
    test_db: str = 'sqlite://:memory:'
    default_size: int = 10
    site_name: str = 'Open Tree Hole'
    email_whitelist: List[str] = []
    verification_code_expires: int = 10
    email_user: str = ''
    email_password: str = get_secret('email_password', '', str)
    email_host: str = ''
    email_port: int = 465
    email_use_tls: bool = True
    email_public_key_path: str = 'data/treehole_demo_public.pem'
    email_private_key_path: str = 'data/treehole_demo_private.pem'
    register_apikey_seed: str = get_secret('register_apikey_seed', '', str)
    kong_url: str = get_secret('kong_url', 'http://kong:8001', str)
    kong_token: str = ''
    authorize_in_debug: bool = True
    redis_url: str = 'redis://redis:6379'


config = Settings(tz=parse_tz())
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
    'timezone': 'utc'
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
