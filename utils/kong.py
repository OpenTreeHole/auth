import asyncio
from typing import List

from aiohttp import ClientSession
from pydantic import BaseModel

from config import config
from utils.exceptions import ServerError

headers = {
    'Authorization': config.kong_token
} if config.kong_token else {}
headers['Content-Type'] = 'application/json'
kong = ClientSession(base_url=config.kong_url, headers=headers)


class JwtCredential(BaseModel):
    id: str
    key: str
    secret: str
    algorithm: str


async def create_user(id: int) -> dict:
    async with kong.put(f'/consumers/{id}', json={}) as r:
        json = await r.json(content_type=None)
        if not r.status == 200:
            raise ServerError(json.get('message'))
        return json


async def create_jwt_credential(id: int) -> JwtCredential:
    async with kong.post(f'/consumers/{id}/jwt', json={}) as r:
        json = await r.json(content_type=None)
        if not r.status == 201:
            raise ServerError(json.get('message'))
        return JwtCredential(**json)


async def list_jwt_credentials(id: int) -> List[dict]:
    async with kong.get(f'/consumers/{id}/jwt') as r:
        json = await r.json(content_type=None)
        if not r.status == 200:
            raise ServerError(json.get('message'))
        data = json.get('data', [])
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
    async def _delete_a_credential(jwt_id: int) -> bool:
        async with kong.delete(f'/consumers/{id}/jwt/{jwt_id}') as r:
            return r.status == 204

    data = await list_jwt_credentials(id)
    tasks = []
    for i in data:
        tasks.append(_delete_a_credential(i['id']))
    results = await asyncio.gather(*tasks)
    return len(list(filter(None, results)))


async def connect_to_gateway():
    async with kong.get('/') as r:
        if not r.status == 200:
            print('Kong API gateway unreachable!')
        else:
            print('gateway connected')

# asyncio.run(connect_to_gateway())
