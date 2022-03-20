import asyncio
from typing import List

import httpx
from pydantic import BaseModel
from sanic import Sanic
from sanic.exceptions import ServerError
from sanic.log import logger

app = Sanic.get_app()
KONG_URL = app.config.get('KONG_URL', 'http://kong:8001')
KONG_TOKEN = app.config.get('KONG_TOKEN', '')
headers = {
    'Authorization': KONG_TOKEN
} if KONG_TOKEN else {}


async def create_user(id: int) -> dict:
    async with httpx.AsyncClient(base_url=KONG_URL, headers=headers) as c:
        r = await c.put(f'/consumers/{id}')
        if not r.status_code == 200:
            raise ServerError(r.json().get('message'), extra=r.json())
        return r.json()


class JwtCredential(BaseModel):
    id: str
    key: str
    secret: str
    algorithm: str


async def create_jwt_credential(id: int) -> JwtCredential:
    async with httpx.AsyncClient(base_url=KONG_URL, headers=headers) as c:
        r = await c.post(f'/consumers/{id}/jwt')
        if not r.status_code == 201:
            raise ServerError(r.json().get('message'), extra=r.json())
        return JwtCredential(**r.json())


async def list_jwt_credentials(id: int) -> List[dict]:
    async with httpx.AsyncClient(base_url=KONG_URL, headers=headers) as c:
        r = await c.get(f'/consumers/{id}/jwt')
        if not r.status_code == 200:
            raise ServerError(r.json().get('message'), extra=r.json())
        data = r.json().get('data', [])
        return data


async def get_jwt_credential(id: int) -> JwtCredential:
    """
                返回用户的第一个 credential
                """
    data = await list_jwt_credentials(id)
    if len(data) == 0:
        return await create_jwt_credential(id)
    return JwtCredential(**data[0])


async def delete_jwt_credentials(id: int) -> int:
    data = await list_jwt_credentials(id)
    num = 0
    tasks = []
    async with httpx.AsyncClient(base_url=KONG_URL, headers=headers) as c:
        for i in data:
            tasks.append(c.delete(f'/consumers/{id}/jwt/{i["id"]}'))
        results = await asyncio.gather(*tasks)
        for r in results:
            if r.status_code == 204:
                num += 1
        return num


async def connect_to_gateway():
    async with httpx.AsyncClient(base_url=KONG_URL, headers=headers) as c:
        r = await c.get('/')
        if not r.status_code == 200:
            logger.error('Kong API gateway unreachable!')
        logger.info('gateway connected')


asyncio.run(connect_to_gateway())
