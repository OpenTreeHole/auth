#  as an oauth2 server
import httpx
from fastapi import Depends
from pydantic import BaseModel

from config import config
from oauth2 import router
from utils.common import get_user_id


class OauthServerRequest(BaseModel):
    scope: str = "id nickname"
    client_id: str


@router.post('/oauth2/server')
async def oauth_server(body: OauthServerRequest, authenticated_userid: int = Depends(get_user_id)):
    authorize_url = 'https://auth.fduhole.com/api/oauth2/authorize'
    payload = {
        "response_type": "code",
        "scope": body.scope,
        "client_id": body.client_id,
        "provision_key": config.provision_key,
        "authenticated_userid": authenticated_userid
    }
    with httpx.AsyncClient() as client:
        res = await client.post(authorize_url, json=payload)
        return res.json()
